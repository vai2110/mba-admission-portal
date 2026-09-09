import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"404.html", "content-audit.html", "college-page-audit-dashboard.html", "index.html"}
BENCHMARKS = {"iim-ahmedabad.html", "sibm-pune.html"}

QUESTION_TERMS = {
    "admission": ["admission", "apply", "application", "selection process", "how to get admission"],
    "eligibility": ["eligibility", "eligible", "qualification", "who can apply"],
    "fees": ["fee", "fees", "tuition", "cost", "total fee"],
    "cutoff": ["cutoff", "cut off", "percentile", "score"],
    "entrance": ["entrance exam", "accepted exam", "cat", "xat", "cmat", "mat", "nmat", "jee", "cuet"],
    "placements": ["placement", "average package", "highest package", "median", "recruiter"],
    "programme": ["programme", "program", "course", "specialization", "curriculum"],
    "location": ["location", "campus", "city", "bengaluru", "bangalore", "delhi", "mumbai", "pune", "noida", "gurugram", "hyderabad", "chennai", "kolkata"],
}


def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def text(soup):
    return clean(soup.get_text(" ", strip=True))


def has_term(value, terms):
    value = value.lower()
    return any(t in value for t in terms)


def audit(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    body = text(soup).lower()
    headings = [clean(h.get_text(" ", strip=True)) for h in soup.find_all(["h2", "h3"])]
    heading_text = " ".join(headings).lower()
    faq = soup.select(".faq")
    answer = soup.select(".answer-first")
    official_links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "official" in a.get_text(" ", strip=True).lower() or "official" in href.lower():
            official_links.append(href)
    schemas = []
    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\\+json", re.I)}):
        try:
            data = json.loads(script.string or script.get_text())
            schemas.append(data)
        except Exception:
            pass
    schema_types = []
    for data in schemas:
        for node in data.get("@graph", []) if isinstance(data, dict) else []:
            if isinstance(node, dict) and node.get("@type"):
                schema_types.extend(node["@type"] if isinstance(node["@type"], list) else [node["@type"]])
        if isinstance(data, dict) and data.get("@type"):
            schema_types.extend(data["@type"] if isinstance(data["@type"], list) else [data["@type"]])

    intent = {k: has_term(body, v) for k, v in QUESTION_TERMS.items()}
    question_headings = [h for h in headings if "?" in h or any(h.lower().startswith(x) for x in ["what ", "how ", "which ", "is ", "can ", "does ", "who ", "when "])]
    is_programme = any(x in path.name.lower() for x in ["mba", "pgdm", "btech", "bca", "bba", "bcom", "mms", "phd", "mtech", "fpm", "executive"])
    is_placement = "placement" in path.name.lower()
    issues = []

    if not answer:
        issues.append("missing_answer_first")
    if len(faq) == 0 and not question_headings:
        issues.append("weak_question_answer_coverage")
    if not official_links:
        issues.append("no_obvious_official_source_link")
    if not intent["admission"] and not is_placement:
        issues.append("admission_intent_missing")
    if not intent["eligibility"] and not is_placement:
        issues.append("eligibility_intent_missing")
    if not intent["fees"] and not is_placement:
        issues.append("fee_intent_missing")
    if is_programme and not intent["programme"]:
        issues.append("programme_intent_missing")
    if is_placement and not intent["placements"]:
        issues.append("placement_intent_missing")
    if not intent["location"]:
        issues.append("location_context_missing")
    if is_programme and "Course" not in schema_types:
        issues.append("course_schema_opportunity")

    score = max(0, 100 - len(issues) * 8)
    return {
        "file": path.name,
        "benchmark": path.name in BENCHMARKS,
        "score": score,
        "page_type": "placement" if is_placement else ("programme" if is_programme else "overview_or_hub"),
        "intent_signals": intent,
        "question_headings": question_headings,
        "faq_count": len(faq),
        "answer_first_count": len(answer),
        "official_link_count": len(official_links),
        "schema_types": sorted(set(schema_types)),
        "issues": issues,
    }


def main():
    pages = [p for p in sorted(ROOT.glob("*.html")) if p.name not in EXCLUDED]
    results = [audit(p) for p in pages]
    counts = Counter(issue for r in results for issue in r["issues"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Site-wide AEO, GEO and student-search-intent audit; benchmark pages are reported but never modified by this audit.",
        "pages_checked": len(results),
        "pages_with_issues": sum(bool(r["issues"]) for r in results),
        "average_score": round(sum(r["score"] for r in results) / len(results), 1) if results else 0,
        "issue_counts": dict(sorted(counts.items())),
        "priority_order": [
            "missing_answer_first",
            "weak_question_answer_coverage",
            "admission_intent_missing",
            "eligibility_intent_missing",
            "fee_intent_missing",
            "placement_intent_missing",
            "location_context_missing",
            "course_schema_opportunity",
            "no_obvious_official_source_link",
        ],
        "pages": results,
    }
    (ROOT / "aeo-geo-intent-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "pages"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
