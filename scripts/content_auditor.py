import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "content-audit-report.json"
EXCLUDED = {"content-audit.html"}

# Deliberately conservative: these patterns flag text for human/ChatGPT review; they do not assert that a claim is false.
GENERIC_PATTERNS = [
    r"one of the (best|leading|premier|top|most prestigious)",
    r"world[- ]class",
    r"state[- ]of[- ]the[- ]art",
    r"rich academic environment",
    r"holistic development",
    r"excellent placement opportunities",
    r"bright career",
    r"dream career",
    r"vibrant campus life",
    r"nurtures (future|young)",
    r"empowers students",
    r"committed to excellence",
    r"aims to provide",
]
PROMO_PATTERNS = [
    r"#?1\s*(in|among|for)",
    r"best[- ]in[- ]class",
    r"unmatched",
    r"guarantee[sd]?",
    r"guaranteed",
    r"assured placement",
    r"no\.\s*1",
    r"number one",
    r"undisputed",
]
INTENT_TERMS = {
    "eligibility": ["eligibility", "who can apply", "qualification"],
    "admission": ["admission process", "selection process", "how to apply", "application"],
    "fees": ["fees", "fee structure", "tuition"],
    "cutoff": ["cutoff", "cut-off", "percentile"],
    "placements": ["placement", "salary", "recruiter", "career outcomes"],
    "scholarship": ["scholarship", "financial aid", "fee waiver"],
    "programme_fit": ["who should apply", "who is this for", "programme fit", "student fit"],
}


def clean_soup(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return soup


def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", normalize(text))
    return [p.strip() for p in parts if len(p.strip()) >= 45]


def source_links(soup):
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        label = normalize(a.get_text(" ", strip=True))
        if href.startswith(("http://", "https://")):
            links.append({"label": label, "url": href})
    return links


def audit_html(path):
    html = path.read_text(encoding="utf-8")
    soup = clean_soup(html)
    page_text = normalize(soup.get_text(" ", strip=True))
    sents = sentences(page_text)
    low_sents = [s.lower() for s in sents]

    generic_hits = []
    for pattern in GENERIC_PATTERNS:
        for m in re.finditer(pattern, page_text, flags=re.I):
            generic_hits.append(normalize(page_text[max(0, m.start()-90):m.end()+130]))

    promo_hits = []
    for pattern in PROMO_PATTERNS:
        for m in re.finditer(pattern, page_text, flags=re.I):
            promo_hits.append(normalize(page_text[max(0, m.start()-90):m.end()+130]))

    # Duplicate detection is conservative: exact normalized sentences only.
    counts = Counter(low_sents)
    duplicate_sents = [s for s, c in counts.items() if c > 1]

    numeric_sents = [s for s in sents if re.search(r"(?:\b20\d{2}\b|₹|%|\b\d+(?:\.\d+)?\s*(?:lakh|crore|LPA|years?|months?|students?|marks?|percentile))", s, re.I)]
    links = source_links(soup)
    official_links = [x for x in links if re.search(r"(?:iima\.ac\.in|iim[a-z-]*\.ac\.in|gov\.in|nta\.ac\.in|cat\.ac\.in|nirfindia\.org)", x["url"], re.I)]

    headings = []
    for h in soup.find_all(["h2", "h3"]):
        title = normalize(h.get_text(" ", strip=True))
        if not title:
            continue
        chunks = []
        for sib in h.next_siblings:
            if getattr(sib, "name", None) in {"h2", "h3"}:
                break
            if hasattr(sib, "get_text"):
                chunks.append(sib.get_text(" ", strip=True))
        section_text = normalize(" ".join(chunks))
        headings.append({"heading": title, "chars": len(section_text), "text": section_text[:280]})

    thin_sections = [x for x in headings if x["chars"] < 180]
    missing = []
    text_lower = page_text.lower()
    for key, terms in INTENT_TERMS.items():
        if not any(t in text_lower for t in terms):
            missing.append(key)

    word_count = len(page_text.split())
    generic_ratio = min(1, len(generic_hits) / max(1, word_count / 350))
    promo_ratio = min(1, len(promo_hits) / max(1, word_count / 500))
    repetition_ratio = min(1, len(duplicate_sents) / max(1, len(sents) / 100))
    thin_ratio = min(1, len(thin_sections) / max(1, len(headings))) if headings else 0
    source_ratio = min(1, len(official_links) / 6)

    # 100 = stronger editorial hygiene. This is a risk score, not a factual accuracy score.
    score = round(max(0, min(100, 100 - generic_ratio*25 - promo_ratio*20 - repetition_ratio*15 - thin_ratio*15 + source_ratio*10)))

    issues = []
    if generic_hits:
        issues.append({"severity":"high","type":"generic","text":f"Found {len(generic_hits)} generic/AI-like phrase patterns.","location":"page text","examples":generic_hits[:5],"recommendation":"Rewrite or remove these sentences so they explain a specific IIM Ahmedabad fact, student implication, or decision point."})
    if promo_hits:
        issues.append({"severity":"high","type":"misleading","text":f"Found {len(promo_hits)} promotional/absolute claim patterns.","location":"page text","examples":promo_hits[:5],"recommendation":"Replace absolute language with precise, sourced wording or remove it."})
    if duplicate_sents:
        issues.append({"severity":"medium","type":"repetition","text":f"Found {len(duplicate_sents)} repeated sentences.","location":"page text","examples":duplicate_sents[:5],"recommendation":"Keep the stronger occurrence and remove the duplicate."})
    if missing:
        issues.append({"severity":"medium","type":"student_intent","text":"Potentially missing student-decision topics: " + ", ".join(missing),"location":"page structure","recommendation":"Add only genuinely relevant sections, using verified official information."})
    if thin_sections:
        issues.append({"severity":"low","type":"structure","text":f"Found {len(thin_sections)} sections with less than 180 characters of supporting text.","location":"sections","examples":[x["heading"] for x in thin_sections[:10]],"recommendation":"Merge thin headings into stronger sections or add decision-useful detail; do not add filler just to increase length."})
    if len(numeric_sents) >= 10 and not official_links:
        issues.append({"severity":"high","type":"unsupported","text":f"Found {len(numeric_sents)} sentences containing dates, figures, percentages or monetary values but no detected official source links.","location":"page text","recommendation":"Manually verify every high-impact figure against the current official source before publication."})
    elif numeric_sents:
        issues.append({"severity":"medium","type":"fact_check","text":f"Found {len(numeric_sents)} sentences containing high-impact figures/dates.","location":"page text","recommendation":"Use the linked official sources to verify each figure and label historical/trend data clearly."})

    recommendations = []
    if generic_hits: recommendations.append({"priority":"high","action":"rewrite_generic_content","count":len(generic_hits)})
    if promo_hits: recommendations.append({"priority":"high","action":"remove_absolute_claims","count":len(promo_hits)})
    if duplicate_sents: recommendations.append({"priority":"medium","action":"remove_repetition","count":len(duplicate_sents)})
    if missing: recommendations.append({"priority":"medium","action":"fill_student_intent_gaps","sections":missing})
    if thin_sections: recommendations.append({"priority":"low","action":"merge_or_strengthen_thin_sections","count":len(thin_sections)})
    recommendations.append({"priority":"high","action":"manual_verify_high_impact_facts","count":len(numeric_sents),"note":"The free audit does not claim these facts are true or false."})

    return {
        "file": path.name,
        "overall_score": score,
        "summary":"Free editorial audit completed. This audit identifies relevance and factual-risk patterns; it does not prove that a factual claim is true.",
        "auto_applied": False,
        "auto_apply_reason":"Free audit mode never rewrites factual content automatically. Review recommendations before applying changes.",
        "metrics":{
            "word_count":word_count,
            "generic_phrase_hits":len(generic_hits),
            "promotional_hits":len(promo_hits),
            "duplicate_sentences":len(duplicate_sents),
            "numeric_or_date_sentences":len(numeric_sents),
            "official_links":len(official_links),
            "all_external_links":len(links),
            "headings":len(headings),
            "thin_sections":len(thin_sections),
            "missing_intent_sections":missing,
        },
        "issues":issues,
        "recommendations":recommendations,
        "verified_facts":[],
        "unverified_claims":[
            {"claim":s,"reason":"Contains a high-impact number/date/figure. The free auditor does not verify external truth.","action":"manual_review"}
            for s in numeric_sents[:50]
        ],
        "replacement_content":[],
        "keep_content":[],
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

    results = []
    for path in files:
        try:
            results.append(audit_html(path))
        except Exception as e:
            results.append({"file":path.name,"overall_score":0,"summary":f"Audit failed: {e}","auto_applied":False,"issues":[{"severity":"high","type":"system","text":str(e),"location":path.name,"recommendation":"Fix the audit configuration and rerun."}]})

    report={"generated_at":datetime.now(timezone.utc).isoformat(),"mode":"free-editorial-audit","pages_audited":len(results),"pages_changed":0,"target_page":target or None,"results":results}
    REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__ == "__main__":
    main()
