import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "content-audit-report.json"
EXCLUDED = {"content-audit.html"}

GENERIC_PATTERNS = [
    r"one of the (?:leading|premier|top|best|renowned|prestigious)",
    r"has carved a niche",
    r"stands as a (?:beacon|symbol)",
    r"plays a vital role",
    r"offers a wide range of",
    r"state[- ]of[- ]the[- ]art",
    r"world[- ]class",
    r"holistic (?:development|education|learning)",
    r"empowers students",
    r"nurtures (?:talent|leaders|students)",
    r"rich learning environment",
    r"vibrant campus life",
    r"dynamic learning environment",
    r"excellent career opportunities",
    r"bright career",
    r"strong foundation",
    r"in today's competitive",
    r"in the ever[- ]changing",
    r"aspiring (?:students|candidates) can",
]
PROMOTIONAL_PATTERNS = [r"best college", r"dream college", r"guarantee(?:d|s)?", r"assured placement", r"100% placement", r"unmatched", r"unparalleled"]

IMPORTANT_TERMS = {
    "eligibility": ["eligibility", "eligible", "qualification"],
    "admission": ["admission", "application", "apply", "selection", "shortlist"],
    "fees": ["fee", "fees", "tuition", "programme fee"],
    "dates": ["date", "deadline", "last date", "schedule", "2026", "2027"],
    "exam": ["cat", "xat", "gmat", "exam", "entrance"],
    "cutoff": ["cutoff", "cut-off", "percentile", "percentile"],
    "placement": ["placement", "salary", "package", "recruiter", "median", "average"],
    "scholarship": ["scholarship", "financial aid", "fee waiver"],
    "fit": ["who should", "suitable", "fit", "consider", "decision", "pros", "cons"],
}


def clean_text(soup):
    clone = BeautifulSoup(str(soup), "html.parser")
    for tag in clone(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return re.sub(r"\s+", " ", clone.get_text(" ", strip=True))


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 35]


def audit(path):
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup)
    sents = sentences(text)
    issues = []
    recommendations = []

    generic_hits = []
    for pattern in GENERIC_PATTERNS:
        generic_hits.extend(re.findall(pattern, text, flags=re.I))
    generic_count = len(generic_hits)
    if generic_count:
        issues.append({"severity":"medium","type":"generic","text":f"Found {generic_count} generic/promo-style phrases that add little college-specific value.","location":"page text","recommendation":"Replace with concrete facts, admission implications, student decision guidance, or remove the sentence."})
        recommendations.append({"priority":"medium","action":"rewrite_generic","reason":"Make claims specific to the institution/programme and useful to an applicant."})

    promo_hits = []
    for pattern in PROMOTIONAL_PATTERNS:
        promo_hits.extend(re.findall(pattern, text, flags=re.I))
    if promo_hits:
        issues.append({"severity":"high","type":"misleading","text":f"Found {len(promo_hits)} high-risk promotional claims such as guarantees/best/unmatched language.","location":"page text","recommendation":"Remove absolute claims unless backed by a clearly cited authoritative source."})
        recommendations.append({"priority":"high","action":"remove_absolute_claims","reason":"Avoid presenting promotional language as an objective fact."})

    # Repeated sentences / near duplicates.
    norm = [re.sub(r"[^a-z0-9 ]", "", s.lower()) for s in sents]
    counts = Counter(norm)
    dupes = [sents[i] for i, n in enumerate(norm) if counts[n] > 1]
    if dupes:
        issues.append({"severity":"medium","type":"repetition","text":f"Found {len(dupes)} repeated sentences/near-identical statements.","location":"page text","recommendation":"Keep the stronger occurrence and remove repeated wording."})
        recommendations.append({"priority":"medium","action":"remove_repetition","reason":"Reduce content bloat and improve scanability."})

    # Numbers and date-like claims need a source trail.
    number_sents = [s for s in sents if re.search(r"(?:₹|rs\.?|%|\b20\d{2}\b|\b\d+(?:\.\d+)?\s*(?:lakh|crore|LPA|years?|months?|seats?)\b)", s, flags=re.I)]
    external_links = [a.get("href") for a in soup.find_all("a", href=True) if a.get("href", "").startswith(("http://", "https://"))]
    official_links = [u for u in external_links if any(x in urlparse(u).netloc.lower() for x in ["iima.ac.in", "iimcal.ac.in", "iimb.ac.in", "iiml.ac.in", "iimk.ac.in", "iimidr.ac.in", "iimtrichy.ac.in", "iims.ac.in", ".gov.in", ".nic.in", "nta.ac.in", "cat.ac.in", "mcc.nic.in"])]
    if number_sents and not official_links:
        issues.append({"severity":"high","type":"unsupported","text":f"Found {len(number_sents)} sentences containing dates/numbers/percentages but no obvious official-source links on the page.","location":"factual claims","recommendation":"Add an official source beside each high-impact figure/date or remove the figure if it cannot be verified."})
        recommendations.append({"priority":"high","action":"add_source_trail","reason":"High-impact facts need an auditable source trail."})

    missing = []
    for section, terms in IMPORTANT_TERMS.items():
        if not any(t in text.lower() for t in terms):
            missing.append(section)
    if missing:
        issues.append({"severity":"medium","type":"student_intent","text":"Potentially missing student-decision sections: " + ", ".join(missing),"location":"page structure","recommendation":"Add only the sections relevant to this programme, using verified institution/exam-authority information."})
        recommendations.append({"priority":"medium","action":"fill_student_intent_gaps","sections":missing,"reason":"Students need decision-useful information, not generic institutional description."})

    # Headings without substantive body text nearby.
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    thin = []
    for h in headings:
        body = []
        for sib in h.find_next_siblings():
            if getattr(sib, "name", "") and re.match(r"^h[1-6]$", sib.name):
                break
            body.append(sib.get_text(" ", strip=True) if getattr(sib, "get_text", None) else "")
        if len(" ".join(body).split()) < 35:
            thin.append(h.get_text(" ", strip=True))
    if thin:
        issues.append({"severity":"low","type":"structure","text":f"Found {len(thin)} headings with thin supporting content.","location":"sections","recommendation":"Strengthen only if the heading answers a real student question; otherwise merge/remove it."})

    # Simple score: start at 100 and penalise risk/bloat, but never claim factual verification.
    score = max(0, 100 - generic_count*3 - len(promo_hits)*8 - len(dupes)*5 - (20 if number_sents and not official_links else 0) - len(missing)*3 - len(thin)*2)
    if not sents:
        score = 0
    summary = "Free editorial audit completed. This audit flags risk and relevance patterns; it does not prove that a factual claim is true."
    return {
        "file": path.name,
        "overall_score": score,
        "summary": summary,
        "auto_applied": False,
        "auto_apply_reason": "Free audit mode never rewrites factual content automatically. Review recommendations before applying changes.",
        "metrics": {"generic_phrase_hits":generic_count,"promotional_hits":len(promo_hits),"duplicate_sentences":len(dupes),"numeric_or_date_sentences":len(number_sents),"official_links":len(official_links),"missing_intent_sections":missing,"thin_sections":len(thin)},
        "issues": issues,
        "recommendations": recommendations,
        "verified_facts": [],
        "unverified_claims": [{"claim":s,"reason":"Contains a high-impact number/date/figure; this free auditor does not verify it against external sources.","action":"manual_review"} for s in number_sents[:30]],
        "replacement_content": [],
        "keep_content": [],
    }


def main():
    target = __import__("os").environ.get("TARGET_PAGE", "").strip()
    if target:
        candidate = (ROOT / target).resolve()
        if candidate.parent != ROOT or candidate.suffix.lower() != ".html" or not candidate.exists():
            raise RuntimeError(f"Invalid TARGET_PAGE: {target}")
        files = [candidate]
    else:
        files = [p for p in sorted(ROOT.glob("*.html")) if p.name not in EXCLUDED]
    results = [audit(p) for p in files]
    report = {"generated_at":datetime.now(timezone.utc).isoformat(),"mode":"free-editorial-audit","pages_audited":len(results),"pages_changed":0,"target_page":target or None,"results":results}
    REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__ == "__main__":
    main()
