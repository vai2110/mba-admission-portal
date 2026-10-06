from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"
EXCLUDED = {
    "404.html", "content-audit.html", "college-page-audit-dashboard.html",
    "github-direct-edit-test.html", "irma-deploy-trigger.html"
}

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.robots = []
        self.links = []
        self.title = ""
        self._title = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        tag = tag.lower()
        if tag == "title":
            self._title = True
        if tag == "link" and "canonical" in (d.get("rel") or "").lower().split():
            if d.get("href"): self.canonical.append(d["href"].strip())
        if tag == "meta" and (d.get("name") or "").lower() == "robots":
            if d.get("content"): self.robots.append(d["content"].strip().lower())
        if tag == "a" and d.get("href"):
            self.links.append(d["href"].strip())

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._title = False

    def handle_data(self, data):
        if self._title:
            self.title += data

def clean_url_for(path):
    return BASE if path.name == "index.html" else BASE + "/" + path.stem

def resolve_local(source, href):
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    p = urlparse(href)
    if p.scheme in {"http", "https"}:
        if p.netloc.lower() not in {"", "collegedecoded.in", "www.collegedecoded.in"}:
            return None
        target = p.path
    else:
        target = p.path
    target = target.split("?", 1)[0].split("#", 1)[0]
    if not target or target == "/":
        return ROOT / "index.html"
    if target.startswith("/"):
        candidate = ROOT / target.lstrip("/")
    else:
        candidate = (source.parent / target).resolve()
    if candidate.suffix == "":
        html = Path(str(candidate) + ".html")
        if html.exists(): return html
        idx = candidate / "index.html"
        if idx.exists(): return idx
    if candidate.exists():
        return candidate
    return None

pages = []
critical = []
titles = {}

for path in ROOT.rglob("*.html"):
    if any(x in {".git", "node_modules", ".github"} for x in path.parts):
        continue
    if path.name.lower() in EXCLUDED:
        continue
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    rel = path.relative_to(ROOT).as_posix()
    indexable = not any("noindex" in x for x in parser.robots)
    expected = clean_url_for(path)
    canonical = parser.canonical[0].rstrip("/") if parser.canonical else ""
    if indexable and canonical != expected.rstrip("/"):
        critical.append(f"canonical mismatch: {rel} -> {canonical or 'MISSING'} (expected {expected})")
    if parser.title.strip():
        titles.setdefault(parser.title.strip(), []).append(rel)
    broken = []
    for href in parser.links:
        # Fragment-only links (e.g. #fees) stay on the same page and are valid anchors.
        if href.startswith("#"):
            continue
        target = resolve_local(path, href)
        if href.startswith(("http://","https://")) and "collegedecoded.in" not in href:
            continue
        if href.startswith("/") or not urlparse(href).scheme:
            if target is None and href not in {"#", "/"}:
                broken.append(href)
    if broken:
        critical.append(f"broken local links: {rel} -> {sorted(set(broken))[:8]}")
    pages.append((rel, indexable))

sitemap = ROOT / "sitemap.xml"
if not sitemap.exists():
    critical.append("sitemap.xml missing after generation")
else:
    xml = sitemap.read_text(encoding="utf-8", errors="ignore")
    locs = re.findall(r"<loc>(.*?)</loc>", xml, re.I)
    for url in locs:
        if ".html" in url.lower():
            critical.append(f"sitemap contains .html URL: {url}")
        if not (url == BASE or url.startswith(BASE + "/")):
            critical.append(f"sitemap contains non-CollegeDecoded URL: {url}")
    # Check that the sitemap does not advertise genuinely thin pages.
    sitemap_thin = []
    for rel, ok in pages:
        if not ok:
            continue
        raw = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        parser_text = re.sub(r"<(script|style|noscript|svg)\\b[^>]*>.*?</\\1>", " ", raw, flags=re.I | re.S)
        words = len(re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", " ", parser_text)).strip().split())
        clean = BASE if rel == "index.html" else BASE + "/" + Path(rel).stem
        if words < 300 and clean in locs:
            sitemap_thin.append(f"{rel} ({words} words)")
    if sitemap_thin:
        critical.append(f"thin page present in sitemap: {sitemap_thin[:10]}")

    indexable_files = {rel for rel, ok in pages if ok}
    # Check that no explicitly noindex root page is present in sitemap.
    for rel, ok in pages:
        if not ok:
            clean = BASE if rel == "index.html" else BASE + "/" + Path(rel).stem
            if clean in locs:
                critical.append(f"noindex page present in sitemap: {rel}")

duplicate_titles = {t: v for t, v in titles.items() if len(v) > 1 and t}
print(f"SEO gate scanned {len(pages)} root/nested HTML pages; sitemap URLs: {len(locs) if sitemap.exists() else 0}")
print(f"Duplicate title groups: {len(duplicate_titles)}")
if duplicate_titles:
    print("WARNING duplicate titles:", list(duplicate_titles.items())[:10])
if critical:
    print("SEO GATE FAILED")
    for item in critical[:100]:
        print("-", item)
    sys.exit(1)
print("SEO GATE PASSED")
