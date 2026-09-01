import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://vai2110.github.io/mba-admission-portal/"
REPORT_PATH = ROOT / "seo-geo-aeo-report.json"
EXCLUDED = {"index.html", "404.html", "content-audit.html"}
ANSWER_CSS = ".answer-first{background:#eef6ff;border:1px solid #cfe0f5;border-radius:8px;padding:13px 15px;margin:0 0 14px;color:#173f82}.answer-first strong{display:block;margin-bottom:4px}.answer-first p{margin:0;font-size:13px;color:#334155}"


def upsert_meta(text, *, name=None, prop=None, content=""):
    key_attr = "name" if name else "property"
    key_value = name or prop
    pattern = rf'<meta\b(?=[^>]*\b{key_attr}=["\']{re.escape(key_value)}["\'])[^>]*>'
    replacement = f'<meta {key_attr}="{html.escape(key_value)}" content="{html.escape(content, quote=True)}">'
    if re.search(pattern, text, flags=re.I | re.S):
        return re.sub(pattern, replacement, text, count=1, flags=re.I | re.S)
    return re.sub(r'</head>', replacement + '</head>', text, count=1, flags=re.I)


def upsert_canonical(text, url):
    pattern = r'<link\b(?=[^>]*\brel=["\'][^"\']*\bcanonical\b[^"\']*["\'])[^>]*>'
    replacement = f'<link rel="canonical" href="{html.escape(url, quote=True)}">'
    if re.search(pattern, text, flags=re.I | re.S):
        return re.sub(pattern, replacement, text, count=1, flags=re.I | re.S)
    return re.sub(r'</head>', replacement + '</head>', text, count=1, flags=re.I)


def extract_title(text, filename):
    m = re.search(r'<title\b[^>]*>(.*?)</title>', text, flags=re.I | re.S)
    return re.sub(r'\s+', ' ', html.unescape(m.group(1))).strip() if m else filename.removesuffix('.html')


def extract_description(text, title):
    # Accept either attribute order: name="description" content="..." or content="..." name="description".
    patterns = [
        r'<meta\b(?=[^>]*\bname=["\']description["\'])[^>]*\bcontent=["\'](.*?)["\'][^>]*>',
        r'<meta\b(?=[^>]*\bcontent=["\'].*?["\'])[^>]*\bname=["\']description["\'][^>]*>',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I | re.S)
        if m:
            # In the second pattern the content value may not be group 1, so locate it explicitly.
            tag = m.group(0)
            cm = re.search(r'\bcontent=["\'](.*?)["\']', tag, flags=re.I | re.S)
            if cm:
                value = re.sub(r'\s+', ' ', html.unescape(cm.group(1))).strip()
                if value:
                    return value
    return title[:155].rstrip()


def extract_location(text):
    m = re.search(r'<div\b[^>]*class=["\']hero-meta["\'][^>]*>(.*?)</div>', text, flags=re.I | re.S)
    if not m:
        return None
    value = re.sub(r'<[^>]+>', ' ', m.group(1))
    value = html.unescape(re.sub(r'\s+', ' ', value)).strip()
    value = re.split(r'\s*[·|]\s*Official Website', value, flags=re.I)[0]
    return value.strip(' ·|-|') or None


def extract_faqs(text):
    items = []
    for block in re.findall(r'<div\b[^>]*class=["\']faq["\'][^>]*>(.*?)</div>', text, flags=re.I | re.S):
        q = re.search(r'<h[1-6]\b[^>]*>(.*?)</h[1-6]>', block, flags=re.I | re.S)
        a = re.search(r'<p\b[^>]*>(.*?)</p>', block, flags=re.I | re.S)
        if q and a:
            clean = lambda x: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()
            items.append((clean(q.group(1)), clean(a.group(1))))
    return items


def add_schema(text, page_url, title, description, location, faq_items):
    text = re.sub(r'<script\b[^>]*data-mba-schema=["\']seo-geo-aeo["\'][^>]*>.*?</script>', '', text, flags=re.I | re.S)
    graph = [
        {"@type": "WebPage", "@id": page_url + "#webpage", "url": page_url, "name": title,
         "description": description, "inLanguage": "en-IN", "isPartOf": {"@id": BASE_URL + "#website"}},
        {"@type": "BreadcrumbList", "@id": page_url + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "MBA Portal", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": title, "item": page_url}]}
    ]
    if location:
        graph.append({"@type": "EducationalOrganization", "name": title.split(":")[0].strip(),
                      "url": page_url, "address": {"@type": "PostalAddress", "addressLocality": location, "addressCountry": "IN"}})
    if faq_items:
        graph.append({"@type": "FAQPage", "@id": page_url + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq_items]})
    payload = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    script = f'<script type="application/ld+json" data-mba-schema="seo-geo-aeo">{payload}</script>'
    return re.sub(r'</head>', script + '</head>', text, count=1, flags=re.I)


def add_answer_first(text, description):
    if re.search(r'class=["\'][^"\']*answer-first', text, flags=re.I):
        return text, False
    block = f'<div class="answer-first" aria-label="Quick answer"><strong>Quick answer</strong><p>{html.escape(description)}</p></div>'
    updated = re.sub(r'(<main\b[^>]*>)', r'\1' + block, text, count=1, flags=re.I)
    return updated, updated != text


def add_css(text):
    if '.answer-first' in text:
        return text, False
    updated = re.sub(r'</style>', ANSWER_CSS + '</style>', text, count=1, flags=re.I)
    return updated, updated != text


def fix_page(path):
    original = path.read_text(encoding="utf-8")
    text = original
    filename = path.name
    page_url = urljoin(BASE_URL, filename)
    title = extract_title(text, filename)
    description = extract_description(text, title)
    location = extract_location(text)
    faq_items = extract_faqs(text)
    changes = []

    new_text = upsert_canonical(text, page_url)
    if new_text != text:
        changes.append("corrected self-referencing canonical URL")
    text = new_text

    for kwargs in [
        {"name": "robots", "content": "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"},
        {"prop": "og:title", "content": title},
        {"prop": "og:description", "content": description},
        {"prop": "og:url", "content": page_url},
        {"prop": "og:type", "content": "website"},
        {"prop": "og:locale", "content": "en_IN"},
        {"name": "twitter:card", "content": "summary"},
        {"name": "twitter:title", "content": title},
        {"name": "twitter:description", "content": description},
    ]:
        text = upsert_meta(text, **kwargs)
    changes.append("standardized social/search metadata")

    text = add_schema(text, page_url, title, description, location, faq_items)
    changes.append("added WebPage and BreadcrumbList schema")
    if location:
        changes.append("added location-aware EducationalOrganization schema")
    if faq_items:
        changes.append(f"added FAQPage schema for {len(faq_items)} visible FAQs")

    text, answer_changed = add_answer_first(text, description)
    if answer_changed:
        changes.append("added answer-first summary for AEO")
    text, css_changed = add_css(text)
    if css_changed:
        changes.append("added answer-first block styling")

    if text != original:
        path.write_text(text, encoding="utf-8")
    return {"file": filename, "changed": text != original, "changes": changes, "canonical": page_url, "location": location}


def main():
    target_pages = os.environ.get("TARGET_PAGES", "").strip()
    if target_pages:
        files = []
        for name in [x.strip() for x in target_pages.splitlines() if x.strip()]:
            path = (ROOT / name).resolve()
            if path.parent != ROOT or path.suffix.lower() != ".html" or not path.exists() or path.name in EXCLUDED:
                continue
            if path.name.startswith("sibm-pune"):
                continue
            files.append(path)
    else:
        files = [p for p in sorted(ROOT.glob("*.html")) if p.name not in EXCLUDED and not p.name.startswith("sibm-pune")]

    results = [fix_page(path) for path in files]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "scope": "today-only pages, excluding SIBM Pune",
              "pages_checked": len(results), "pages_changed": sum(1 for r in results if r["changed"]), "results": results,
              "principles": ["Preserve visible factual copy.", "Use self-referencing canonicals.",
                             "Add answer-first AEO signals.", "Add institute/location GEO signals without inventing street addresses."]}
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
