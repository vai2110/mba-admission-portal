import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

OPENAI_API_URL = "https://api.openai.com/v1/responses"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "content-audit-report.json"

EXCLUDED = {"content-audit.html"}

SYSTEM_PROMPT = r'''
You are the editorial quality and fact-verification agent for an Indian MBA admissions website.
Your job is to improve student decision usefulness, not to make pages longer.

STRICT EDITORIAL RULES:
1. Remove or rewrite generic AI-like filler, broad motivational statements, obvious definitions, repeated claims, and content that could apply to any college/exam.
2. Every substantial paragraph should answer a real student question: eligibility, application route, selection process, fees, deadlines, exam acceptance, cutoff interpretation, placements, scholarships, campus/program fit, or a practical decision implication.
3. Never invent numbers, rankings, cutoffs, fees, dates, placement figures, selection weights, scholarship amounts, accreditation claims, faculty claims, facilities, recruiters, or admission rules.
4. Treat any unsupported exact figure or date as HIGH RISK. Prefer deleting it or replacing it with a clearly qualified statement unless an authoritative source verifies it.
5. Prefer official institution, exam authority, government, regulator, counselling body, or official placement report sources. Do not use coaching sites as factual authority when an official source exists.
6. Do not turn uncertainty into certainty. If a fact cannot be verified, mark it for review rather than guessing.
7. Preserve useful HTML structure, internal links, tables, styling hooks, accessibility attributes, and existing navigation.
8. Do not change CSS/design unless a content change genuinely requires it.
9. Do not keyword-stuff. Use natural student-first language.
10. For each proposed edit, explain the student value gained.

OUTPUT ONLY valid JSON with this shape:
{
  "overall_score": 0-100,
  "summary": "...",
  "issues": [{"severity":"high|medium|low","type":"generic|irrelevant|unsupported|misleading|repetition|student_intent|structure","text":"...","location":"...","recommendation":"..."}],
  "verified_facts": [{"claim":"...","source":"..."}],
  "unverified_claims": [{"claim":"...","reason":"..."}],
  "replacement_content": [{"location":"...","old_text":"...","new_text":"...","reason":"..."}],
  "keep_content": [{"location":"...","reason":"..."}],
  "revised_html": "FULL HTML DOCUMENT"
}
'''


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def extract_urls(html: str):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if href.startswith("http://") or href.startswith("https://"):
            urls.append(href)
    return list(dict.fromkeys(urls))[:30]


def fetch_source(url: str):
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "MBA-Portal-Content-Auditor/1.0"})
        if r.status_code >= 400:
            return {"url": url, "status": r.status_code, "text": ""}
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        return {"url": url, "status": r.status_code, "text": text[:12000]}
    except Exception as e:
        return {"url": url, "status": 0, "text": "", "error": str(e)}


def call_model(html: str, path: str):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY GitHub secret is not configured")

    urls = extract_urls(html)
    sources = [fetch_source(u) for u in urls]
    payload = {
        "model": MODEL,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Audit this page: {path}\n\n"
                f"HTML:\n{html[:180000]}\n\n"
                f"Extracted linked source material (may be incomplete; use only as evidence):\n"
                f"{json.dumps(sources, ensure_ascii=False)[:100000]}"
            )}
        ],
        "text": {"format": {"type": "json_object"}},
        "max_output_tokens": 50000,
    }
    r = requests.post(OPENAI_API_URL, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=240)
    r.raise_for_status()
    data = r.json()
    text = data.get("output_text")
    if not text:
        # Fallback for response shapes where output_text is absent.
        chunks = []
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    chunks.append(c.get("text", ""))
        text = "".join(chunks)
    if not text:
        raise RuntimeError("OpenAI response did not contain output text")
    return json.loads(text)


def audit_file(path: Path):
    original = path.read_text(encoding="utf-8")
    result = call_model(original, str(path.relative_to(ROOT)))
    revised = result.get("revised_html", "").strip()
    # Safety gate: never replace a page with malformed or suspiciously short HTML.
    if revised and "<html" in revised.lower() and len(revised) >= max(1000, int(len(original) * 0.55)):
        path.write_text(revised, encoding="utf-8")
        result["auto_applied"] = True
    else:
        result["auto_applied"] = False
        result["auto_apply_reason"] = "Safety gate rejected the proposed HTML; report retained for review."
    return result


def main():
    html_files = sorted(ROOT.glob("*.html"))
    results = []
    for path in html_files:
        if path.name in EXCLUDED:
            continue
        try:
            results.append(audit_file(path))
            results[-1]["file"] = path.name
        except Exception as e:
            results.append({"file": path.name, "overall_score": 0, "summary": f"Audit failed: {e}", "issues": [{"severity": "high", "type": "system", "text": str(e), "location": path.name, "recommendation": "Review the workflow configuration and rerun the audit."}], "auto_applied": False})

    report = {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "pages_audited": len(results),
        "pages_changed": sum(1 for x in results if x.get("auto_applied")),
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
