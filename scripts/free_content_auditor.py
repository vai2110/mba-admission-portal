import json
import os
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
    r"one of the (?:leading|premier|top|best|renowned|prestigious)", r"has carved a niche",
    r"stands as a (?:beacon|symbol)", r"plays a vital role", r"offers a wide range of",
    r"state[- ]of[- ]the[- ]art", r"world[- ]class", r"holistic (?:development|education|learning)",
    r"empowers students", r"nurtures (?:talent|leaders|students)", r"rich learning environment",
    r"vibrant campus life", r"dynamic learning environment", r"excellent career opportunities",
    r"bright career", r"strong foundation", r"in today's competitive", r"in the ever[- ]changing",
    r"aspiring (?:students|candidates) can",
]
PROMOTIONAL_PATTERNS = [
    r"best college", r"dream college", r"assured placement", r"100% placement",
    r"unmatched", r"unparalleled", r"number one", r"no\.\s*1", r"guarantee(?:d|s)?"
]
NEGATED_PROMO_MARKERS = [
    "does not guarantee", "do not guarantee", "doesn't guarantee", "don't guarantee",
    "not guarantee", "not guaranteed", "cannot guarantee", "can't guarantee",
    "does not by itself guarantee", "does not automatically guarantee",
]
IMPORTANT_TERMS = {
    "eligibility": ["eligibility", "eligible", "qualification"], "admission": ["admission", "application", "apply", "selection", "shortlist"],
    "fees": ["fee", "fees", "tuition", "programme fee"], "dates": ["date", "deadline", "last date", "schedule"],
    "exam": ["cat", "xat", "gmat", "exam", "entrance"], "cutoff": ["cutoff", "cut-off", "percentile"],
    "placement": ["placement", "salary", "package", "recruiter", "median", "average"],
    "scholarship": ["scholarship", "financial aid", "fee waiver"],
    "fit": ["who should", "suitable", "fit", "consider", "decision", "pros", "cons"],
}


def clean_text(soup):
    clone = BeautifulSoup(str(soup), "html.parser")
    for tag in clone(["script", "style", "noscript", "svg", "nav", "header", "footer"]):
        tag.decompose()
    return re.sub(r"\s+", " ", clone.get_text(" ", strip=True))


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 35]


def is_negated_guarantee_sentence(sentence):
    normalized = re.sub(r"\s+", " ", sentence.lower())
    return any(marker in normalized for marker in NEGATED_PROMO_MARKERS)


def audit(path):
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup)
    lower = text.lower()
    sents = sentences(text)
    issues, recommendations = [], []

    generic_examples = []
    for pattern in GENERIC_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.I):
            generic_examples.append(text[max(0, m.start()-80):m.end()+120].strip())
    generic_count = len(generic_examples)
    if generic_count:
        issues.append({"severity":"high","type":"generic","text":f"Found {generic_count} generic/AI-style phrase patterns.","location":"page text","examples":generic_examples[:6],"recommendation":"Replace each sentence with a college-specific fact, student implication or decision aid; otherwise remove it."})
        recommendations.append({"priority":"high","action":"rewrite_generic","count":generic_count,"reason":"Make the page specific and useful instead of interchangeable with another college page."})

    promo_examples = []
    for pattern in PROMOTIONAL_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.I):
            if pattern == r"guarantee(?:d|s)?":
                # Evaluate the complete sentence rather than a small character window.
                containing_sentence = next((s for s in sents if s.lower().find(m.group(0).lower()) >= 0), "")
                if containing_sentence and is_negated_guarantee_sentence(containing_sentence):
                    continue
            promo_examples.append(text[max(0, m.start()-80):m.end()+120].strip())
    if promo_examples:
        issues.append({"severity":"high","type":"misleading","text":f"Found {len(promo_examples)} promotional/absolute claim patterns.","location":"page text","examples":promo_examples[:6],"recommendation":"Use precise, sourced language. Avoid guarantees, superlatives and absolute claims. Negated cautionary statements such as 'does not guarantee a call' are not promotional claims."})
        recommendations.append({"priority":"high","action":"remove_absolute_claims","count":len(promo_examples)})

    norm = [re.sub(r"[^a-z0-9 ]", "", s.lower()) for s in sents]
    counts = Counter(norm)
    dupes = list(dict.fromkeys(sents[i] for i, n in enumerate(norm) if counts[n] > 1))
    if dupes:
        issues.append({"severity":"medium","type":"repetition","text":f"Found {len(dupes)} repeated sentences/near-identical statements.","location":"page text","examples":dupes[:5],"recommendation":"Keep the stronger occurrence and remove the duplicate."})
        recommendations.append({"priority":"medium","action":"remove_repetition","count":len(dupes)})

    number_sents = [s for s in sents if re.search(r"(?:₹|rs\.?|%|\b20\d{2}\b|\b\d+(?:\.\d+)?\s*(?:lakh|crore|LPA|years?|months?|seats?|students?|marks?)\b)", s, flags=re.I)]
    external_links = [a.get("href") for a in soup.find_all("a", href=True) if a.get("href", "").startswith(("http://", "https://"))]
    official_domains = ["iima.ac.in", "iimb.ac.in", "iimcal.ac.in", "iiml.ac.in", "iimk.ac.in", "iimidr.ac.in", ".gov.in", ".nic.in", "nta.ac.in", "cat.ac.in", "nirfindia.org"]
    official_links = [u for u in external_links if any(x in urlparse(u).netloc.lower() for x in official_domains)]
    if number_sents:
        severity = "high" if not official_links else "medium"
        issues.append({"severity":severity,"type":"fact_check","text":f"Found {len(number_sents)} sentences containing dates, figures, percentages or monetary values.","location":"factual claims","recommendation":"Manually verify high-impact claims against the current authoritative source. The free audit does not determine whether the number is true."})
        recommendations.append({"priority":"high","action":"manual_verify_high_impact_facts","count":len(number_sents),"official_source_links":len(official_links)})

    missing = [section for section, terms in IMPORTANT_TERMS.items() if not any(t in lower for t in terms)]
    if missing:
        issues.append({"severity":"medium","type":"student_intent","text":"Potentially missing student-decision topics: " + ", ".join(missing),"location":"page structure","recommendation":"Add only relevant sections and use verified information; do not add generic filler."})
        recommendations.append({"priority":"medium","action":"fill_student_intent_gaps","sections":missing})

    thin = []
    content = soup.select(".main-section, main article, article")
    for section in content:
        h = section.find(["h2", "h3"])
        if not h:
            continue
        body = section.get_text(" ", strip=True)
        if len(body.split()) < 45:
            thin.append(h.get_text(" ", strip=True))
    if thin:
        issues.append({"severity":"low","type":"structure","text":f"Found {len(thin)} major sections with thin supporting content.","location":"main content sections","examples":thin[:10],"recommendation":"Merge thin sections or add specific student-useful information; never add filler just to increase length."})
        recommendations.append({"priority":"low","action":"merge_or_strengthen_thin_sections","count":len(thin)})

    word_count = len(text.split())
    penalty = min(35, generic_count * 5) + min(25, len(promo_examples) * 8) + min(15, len(dupes) * 5) + min(12, len(missing) * 2) + min(8, len(thin) * 2)
    score = max(0, min(100, 100 - penalty)) if word_count else 0

    return {
        "file": path.name, "overall_score": score,
        "summary":"Free editorial audit completed. It identifies generic/repetitive/promotional patterns and factual-risk areas; it does not prove a factual claim true or false.",
        "auto_applied":False,
        "auto_apply_reason":"Free audit mode never rewrites factual content automatically. Review recommendations before applying changes.",
        "metrics":{"word_count":word_count,"generic_phrase_hits":generic_count,"promotional_hits":len(promo_examples),"duplicate_sentences":len(dupes),"numeric_or_date_sentences":len(number_sents),"official_links":len(official_links),"all_external_links":len(external_links),"missing_intent_sections":missing,"thin_sections":len(thin)},
        "issues":issues,"recommendations":recommendations,"verified_facts":[],
        "unverified_claims":[{"claim":s,"reason":"Contains a high-impact number/date/figure; free audit does not verify external truth.","action":"manual_review"} for s in number_sents[:50]],
        "replacement_content":[],"keep_content":[]
    }


def main():
    target = os.environ.get("TARGET_PAGE", "").strip()
    if target:
        candidate = (ROOT / target).resolve()
        if candidate.parent != ROOT or candidate.suffix.lower() != ".html" or not candidate.exists():
            raise RuntimeError(f"Invalid TARGET_PAGE: {target}")
        files = [candidate]
    else:
        files = [p for p in sorted(ROOT.glob("*.html")) if p.name not in EXCLUDED]
    results = [audit(p) for p in files]
    report={"generated_at":datetime.now(timezone.utc).isoformat(),"mode":"free-editorial-audit","pages_audited":len(results),"pages_changed":0,"target_page":target or None,"results":results}
    REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__ == "__main__":
    main()
