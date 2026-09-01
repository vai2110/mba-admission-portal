import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://vai2110.github.io/mba-admission-portal/"
REPORT_PATH = ROOT / "seo-geo-aeo-report.json"
EXCLUDED = {"index.html", "404.html", "content-audit.html"}


def get_meta(soup, name=None, prop=None):
    if name:
        return soup.find("meta", attrs={"name": name})
    return soup.find("meta", attrs={"property": prop})


def upsert_meta(soup, *, name=None, prop=None, content=""):
    tag = get_meta(soup, name=name, prop=prop)
    if tag is None:
        attrs = {"name": name} if name else {"property": prop}
        tag = soup.new_tag("meta", attrs=attrs)
        soup.head.append(tag)
    tag["content"] = content


def canonicalize(soup, url):
    link = soup.find("link", rel=lambda value: value and "canonical" in value)
    if link is None:
        link = soup.new_tag("link", rel="canonical")
        soup.head.append(link)
    changed = link.get("href") != url
    link["href"] = url
    return changed


def hero_location(soup):
    meta = soup.select_one(".hero-meta")
    if not meta:
        return None
    text = meta.get_text(" ", strip=True)
    text = re.sub(r"\s*[·|]\s*Official Website.*$", "", text, flags=re.I)
    return text.strip(" ·|-|") or None


def add_jsonld(soup, page_url, title, description, location, faq_items):
    # Remove only our generated nodes so reruns remain deterministic.
    for node in soup.find_all("script", attrs={"data-mba-schema": "seo-geo-aeo"}):
        node.decompose()

    graph = [
        {
            "@type": "WebPage",
            "@id": page_url + "#webpage",
            "url": page_url,
            "name": title,
            "description": description,
            "inLanguage": "en-IN",
            "isPartOf": {"@id": BASE_URL + "#website"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": page_url + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "MBA Portal", "item": BASE_URL},
                {"@type": "ListItem", "position": 2, "name": title, "item": page_url},
            ],
        },
    ]

    if location:
        graph.append({
            "@type": "EducationalOrganization",
            "name": title.split(":")[0].strip(),
            "url": page_url,
            "address": {"@type": "PostalAddress", "addressLocality": location, "addressCountry": "IN"},
        })

    if faq_items:
        graph.append({
            "@type": "FAQPage",
            "@id": page_url + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faq_items
            ],
        })

    script = soup.new_tag("script", type="application/ld+json")
    script["data-mba-schema"] = "seo-geo-aeo"
    script.string = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    soup.head.append(script)


def fix_page(path):
    original = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(original, "html.parser")
    filename = path.name
    page_url = urljoin(BASE_URL, filename)
    title = soup.title.get_text(" ", strip=True) if soup.title else filename.removesuffix(".html")
    description = (get_meta(soup, name="description") or {}).get("content", "").strip()
    if not description:
        hero_p = soup.select_one(".hero p")
        description = hero_p.get_text(" ", strip=True) if hero_p else title
        description = description[:155].rstrip()

    changes = []
    if canonicalize(soup, page_url):
        changes.append("corrected self-referencing canonical URL")

    upsert_meta(soup, name="robots", content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1")
    upsert_meta(soup, prop="og:title", content=title)
    upsert_meta(soup, prop="og:description", content=description)
    upsert_meta(soup, prop="og:url", content=page_url)
    upsert_meta(soup, prop="og:type", content="website")
    upsert_meta(soup, prop="og:locale", content="en_IN")
    upsert_meta(soup, name="twitter:card", content="summary")
    upsert_meta(soup, name="twitter:title", content=title)
    upsert_meta(soup, name="twitter:description", content=description)
    changes.append("standardized social/search metadata")

    location = hero_location(soup)
    faq_items = []
    for faq in soup.select(".faq"):
        q = faq.find(re.compile("^h[1-6]$"))
        p = faq.find("p")
        if q and p:
            faq_items.append((q.get_text(" ", strip=True), p.get_text(" ", strip=True)))
    add_jsonld(soup, page_url, title, description, location, faq_items)
    changes.append("added WebPage, BreadcrumbList and location-aware EducationalOrganization schema")
    if faq_items:
        changes.append(f"added FAQPage schema for {len(faq_items)} visible FAQs")

    # Add a compact answer-first label outside the hero only when the page does not already have one.
    main = soup.find("main")
    if main and not main.select_one(".answer-first"):
        first_section = main.find("section", class_="section")
        if first_section:
            block = soup.new_tag("div", attrs={"class": "answer-first", "aria-label": "Quick answer"})
            strong = soup.new_tag("strong")
            strong.string = "Quick answer"
            p = soup.new_tag("p")
            p.string = description
            block.append(strong)
            block.append(p)
            first_section.insert_before(block)
            changes.append("added answer-first summary for AEO")

    # Add lightweight styling for the new answer block without touching the approved hero.
    style = soup.find("style", string=lambda text: text and ".answer-first" in text)
    if not style:
        styles = soup.find("style")
        if styles:
            styles.string = (styles.string or "") + ".answer-first{background:#eef6ff;border:1px solid #cfe0f5;border-radius:8px;padding:13px 15px;margin:0 0 14px;color:#173f82}.answer-first strong{display:block;margin-bottom:4px}.answer-first p{margin:0;font-size:13px;color:#334155}"
            changes.append("added answer-first block styling")

    updated = str(soup)
    changed = updated != original
    if changed:
        path.write_text(updated, encoding="utf-8")
    return {"file": filename, "changed": changed, "changes": changes, "canonical": page_url, "location": location}


def main():
    target_pages = os.environ.get("TARGET_PAGES", "").strip()
    if target_pages:
        names = [x.strip() for x in target_pages.splitlines() if x.strip()]
        files = []
        for name in names:
            path = (ROOT / name).resolve()
            if path.parent != ROOT or path.suffix.lower() != ".html" or not path.exists() or path.name in EXCLUDED:
                continue
            if path.name.startswith("sibm-pune"):
                continue
            files.append(path)
    else:
        files = [p for p in sorted(ROOT.glob("*.html")) if p.name not in EXCLUDED and not p.name.startswith("sibm-pune")]

    results = [fix_page(path) for path in files]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "today-only pages, excluding SIBM Pune",
        "pages_checked": len(results),
        "pages_changed": sum(1 for r in results if r["changed"]),
        "results": results,
        "principles": [
            "Preserve visible factual copy; do not invent fees, dates, cutoffs, placements or recruiter claims.",
            "Use self-referencing canonical URLs on every leaf page.",
            "Add answer-first metadata and visible summary for AEO.",
            "Add institute/location entity signals for GEO without claiming an exact street address.",
        ],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
