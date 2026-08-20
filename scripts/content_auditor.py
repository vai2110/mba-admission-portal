import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OPENAI_API_URL = "https://api.openai.com/v1/responses"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "content-audit-report.json"
EXCLUDED = {"content-audit.html"}

SYSTEM_PROMPT = r'''
You are the senior editorial quality and fact-verification agent for an Indian MBA admissions website.
Your objective is student usefulness and factual reliability, not word count or SEO padding.

NON-NEGOTIABLE RULES:
1. Remove or rewrite generic AI-like filler, motivational fluff, obvious textbook definitions, repetition, and statements that could apply to almost any MBA college/exam.
2. Make content specific to the page entity and the student's decision. Explain practical implications where evidence supports them.
3. Never invent or estimate facts. Never fabricate fees, dates, cutoffs, rankings, placement figures, recruiters, selection weights, eligibility rules, scholarship amounts, programme names, facilities, accreditation, faculty claims, or admission routes.
4. Every exact/high-impact factual claim must be supported by reliable evidence. Prefer the official institution, exam authority, government/regulator, counselling authority, or official placement/scholarship document. Use reputable secondary sources only when primary evidence is unavailable, and mark the limitation.
5. If a claim cannot be verified, do not polish it into certainty. Flag it as unverified and either remove it or rewrite it cautiously without introducing a new factual claim.
6. Distinguish admission-cycle facts from historical/trend information. Never present an old cutoff, fee, date, or placement number as current.
7. Do not make causal claims such as 'best for', 'guarantees', 'assures', or 'leads to' unless the evidence directly supports them.
8. Preserve existing HTML structure, CSS, navigation, internal links, IDs, tables and accessibility. Content improvements should not redesign the page.
9. Do not keyword-stuff. Write naturally for an Indian MBA aspirant.
10. Prioritise high-value sections: eligibility, application route, selection process, fees, important dates, accepted exams, cutoff interpretation, placements, scholarships, programme fit, and decision guidance.
11. Do not add a generic conclusion just to increase length.
12. Before changing a factual statement, actively verify it using web search and the supplied linked sources. Search official domains first when the entity is identifiable.

OUTPUT ONLY valid JSON matching the requested keys. Do not wrap JSON in markdown fences.
'''


def extract_urls(html):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if href.startswith(("http://", "https://")):
            urls.append(href)
    return list(dict.fromkeys(urls))[:30]


def fetch_source(url):
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "MBA-Portal-Content-Auditor/1.0"})
        if r.status_code >= 400:
            return {"url": url, "status": r.status_code, "text": ""}
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        return {"url": url, "status": r.status_code, "text": text[:14000]}
    except Exception as e:
        return {"url": url, "status": 0, "text": "", "error": str(e)}


def call_model(html, path):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI secret is not available to the audit process")

    linked_sources = [fetch_source(u) for u in extract_urls(html)]
    user_content = (
        f"Audit page: {path}\n\n"
        f"Existing HTML:\n{html[:200000]}\n\n"
        f"Linked source material (supporting evidence only; may be incomplete):\n"
        f"{json.dumps(linked_sources, ensure_ascii=False)[:110000]}\n\n"
        "For every high-impact factual claim, use the web search tool to verify current authoritative evidence before editing. "
        "Search official domains first. Do not invent missing data. "
        "Return a JSON object with: overall_score, summary, issues, verified_facts, unverified_claims, replacement_content, keep_content, revised_html."
    )

    payload = {
        "model": MODEL,
        "tools": [{"type": "web_search_preview"}],
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "max_output_tokens": 50000,
    }
    r = requests.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=300,
    )
    if r.status_code >= 400:
        try:
            detail = r.json().get("error", {})
            message = detail.get("message") or detail.get("code") or r.text[:500]
        except Exception:
            message = r.text[:500]
        raise RuntimeError(f"OpenAI API {r.status_code}: {message}")

    data = r.json()
    text = data.get("output_text")
    if not text:
        chunks = []
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    chunks.append(c.get("text", ""))
        text = "".join(chunks)
    if not text:
        raise RuntimeError("OpenAI response did not contain output text")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"OpenAI returned non-JSON audit output: {e}") from e


def audit_file(path):
    original = path.read_text(encoding="utf-8")
    result = call_model(original, str(path.relative_to(ROOT)))
    revised = result.get("revised_html", "").strip()
    if revised and "<html" in revised.lower() and len(revised) >= max(1000, int(len(original) * 0.55)):
        path.write_text(revised, encoding="utf-8")
        result["auto_applied"] = True
    else:
        result["auto_applied"] = False
        result["auto_apply_reason"] = "Safety gate rejected the proposed HTML; report retained for review."
    return result


def main():
    target = os.getenv("TARGET_PAGE", "").strip()
    if target:
        candidate = (ROOT / target).resolve()
        if candidate.parent != ROOT or candidate.suffix.lower() != ".html" or not candidate.exists():
            raise RuntimeError(f"Invalid TARGET_PAGE: {target}")
        html_files = [candidate]
    else:
        html_files = [p for p in sorted(ROOT.glob("*.html")) if p.name not in EXCLUDED]

    results = []
    for path in html_files:
        if path.name in EXCLUDED:
            continue
        try:
            item = audit_file(path)
            item["file"] = path.name
            results.append(item)
        except Exception as e:
            results.append({
                "file": path.name,
                "overall_score": 0,
                "summary": f"Audit failed: {e}",
                "issues": [{"severity":"high","type":"system","text":str(e),"location":path.name,"recommendation":"Review the workflow configuration and rerun the audit."}],
                "auto_applied": False,
            })

    from datetime import datetime, timezone
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages_audited": len(results),
        "pages_changed": sum(1 for x in results if x.get("auto_applied")),
        "target_page": target or None,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
