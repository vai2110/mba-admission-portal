import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://vai2110.github.io/mba-admission-portal/"
EXCLUDED = {"404.html"}
BENCHMARKS = {"iim-ahmedabad.html", "sibm-pune.html"}

def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()

def local_target(href, current):
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc and parsed.netloc != "vai2110.github.io": return None
        path = parsed.path
        prefix = "/mba-admission-portal/"
        if not path.startswith(prefix): return None
        path = path[len(prefix):]
    else:
        path = parsed.path
    if not path: return "index.html"
    target = Path(path.lstrip("/"))
    if target.suffix == "": target = target / "index.html"
    try:
        resolved = (current.parent / target).resolve()
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")

def audit_page(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    title = clean(soup.title.get_text(" ", strip=True)) if soup.title else None
    descriptions = soup.find_all("meta", attrs={"name": re.compile(r"^description$", re.I)})
    desc = clean(descriptions[0].get("content")) if descriptions else None
    robots = [clean(x.get("content")) for x in soup.find_all("meta", attrs={"name": re.compile(r"^robots$", re.I)})]
    canonicals = [clean(x.get("href")) for x in soup.find_all("link", attrs={"rel": lambda x: x and "canonical" in x})]
    h1s = [clean(x.get_text(" ", strip=True)) for x in soup.find_all("h1")]
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_url = soup.find("meta", attrs={"property": "og:url"})
    twitter_card = soup.find("meta", attrs={"name": "twitter:card"})
    schemas = soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)})
    images = soup.find_all("img")
    missing_alt = [str(img.get("src", ""))[:180] for img in images if img.get("alt") is None]
    broken = []
    for anchor in soup.find_all("a", href=True):
        target = local_target(anchor.get("href"), path)
        if target and not (ROOT / target).exists(): broken.append(anchor.get("href"))
    expected = BASE_URL + path.name
    return {
        "file": path.name, "benchmark": path.name in BENCHMARKS,
        "title": title, "title_length": len(title or ""),
        "description": desc, "description_length": len(desc or ""), "description_count": len(descriptions),
        "canonical": canonicals[0] if canonicals else None, "canonical_count": len(canonicals),
        "canonical_self": bool(canonicals and canonicals[0].rstrip("/") == expected.rstrip("/")),
        "h1_count": len(h1s), "h1": h1s[0] if h1s else None,
        "lang": clean(soup.html.get("lang")) if soup.html else None,
        "viewport": bool(soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})),
        "robots": robots, "indexable": not any("noindex" in x.lower() for x in robots),
        "og_title": bool(og_title and clean(og_title.get("content"))),
        "og_description": bool(og_desc and clean(og_desc.get("content"))),
        "og_url": bool(og_url and clean(og_url.get("content"))),
        "twitter_card": bool(twitter_card and clean(twitter_card.get("content"))),
        "jsonld_blocks": len(schemas), "images": len(images), "images_missing_alt": len(missing_alt),
        "broken_local_links": sorted(set(broken)),
    }

def main():
    pages = [p for p in sorted(ROOT.glob("*.html")) if p.name not in EXCLUDED]
    results = [audit_page(p) for p in pages]
    titles, canonicals = defaultdict(list), defaultdict(list)
    for r in results:
        if r["title"]: titles[r["title"]].append(r["file"])
        if r["canonical"]: canonicals[r["canonical"]].append(r["file"])
    for r in results:
        r["duplicate_title"] = len(titles.get(r["title"], [])) > 1 if r["title"] else False
        r["duplicate_canonical"] = len(canonicals.get(r["canonical"], [])) > 1 if r["canonical"] else False
        issues = []
        if not r["title"]: issues.append("missing_title")
        elif not 30 <= r["title_length"] <= 65: issues.append("title_length")
        if r["description_count"] != 1: issues.append("description_count")
        elif not 120 <= r["description_length"] <= 170: issues.append("description_length")
        if not r["canonical_self"]: issues.append("canonical")
        if r["h1_count"] != 1: issues.append("h1_count")
        if not r["lang"]: issues.append("lang")
        if not r["viewport"]: issues.append("viewport")
        if not r["indexable"]: issues.append("noindex")
        if not r["og_title"]: issues.append("og_title")
        if not r["og_description"]: issues.append("og_description")
        if not r["og_url"]: issues.append("og_url")
        if not r["twitter_card"]: issues.append("twitter_card")
        if r["jsonld_blocks"] == 0: issues.append("jsonld")
        if r["images_missing_alt"]: issues.append("image_alt")
        if r["broken_local_links"]: issues.append("broken_local_links")
        if r["duplicate_title"]: issues.append("duplicate_title")
        if r["duplicate_canonical"]: issues.append("duplicate_canonical")
        r["issues"] = issues
    counts = Counter(issue for r in results for issue in r["issues"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Root-level HTML technical SEO audit; benchmark pages are audited but never modified by this workflow.",
        "pages_checked": len(results), "pages_with_issues": sum(bool(r["issues"]) for r in results),
        "issue_counts": dict(sorted(counts.items())),
        "duplicate_titles": {k: v for k, v in titles.items() if len(v) > 1},
        "duplicate_canonicals": {k: v for k, v in canonicals.items() if len(v) > 1}, "pages": results,
    }
    (ROOT / "technical-seo-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"pages", "duplicate_titles", "duplicate_canonicals"}}, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
