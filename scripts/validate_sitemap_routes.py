#!/usr/bin/env python3
"""Fail the production build if XML sitemaps advertise missing or non-canonical routes."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
NEWS_SITEMAP = ROOT / "news-sitemap.xml"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.robots = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append((attrs.get("href") or "").strip())
        if tag.lower() == "meta" and attrs.get("name", "").lower() in {"robots", "googlebot"}:
            self.robots.append((attrs.get("content") or "").lower())

def read_sitemap(path):
    if not path.is_file():
        raise SystemExit(f"SITEMAP VALIDATION FAILED: missing {path.name}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise SystemExit(f"SITEMAP VALIDATION FAILED: invalid XML in {path.name}: {exc}")
    entries = []
    for node in root.findall("s:url", NS):
        entries.append(((node.findtext("s:loc", default="", namespaces=NS) or "").strip(),
                        (node.findtext("s:lastmod", default="", namespaces=NS) or "").strip()))
    return entries

def route_file(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "collegedecoded.in":
        return None
    if parsed.query or parsed.fragment or re.search(r"\.html$", parsed.path, re.I):
        return None
    path = parsed.path.strip("/")
    if not path:
        candidates = [ROOT / "index.html"]
    elif path == "news":
        candidates = [ROOT / "news" / "index.html"]
    elif path.startswith("news/"):
        candidates = [ROOT / (path + ".html")]
    else:
        candidates = [ROOT / (path + ".html"), ROOT / path / "index.html"]
    return next((p for p in candidates if p.is_file()), None)

def validate_sitemap(path, main_urls=None, require_lastmod=True):
    entries = read_sitemap(path)
    errors = []
    urls = [url for url, _ in entries]
    if len(urls) != len(set(urls)):
        errors.append(f"{path.name} contains duplicate URLs")
    for url, lastmod in entries:
        parsed = urlparse(url)
        if not url or parsed.scheme != "https" or parsed.netloc.lower() != "collegedecoded.in":
            errors.append(f"invalid canonical origin: {url}")
            continue
        if parsed.query or parsed.fragment or re.search(r"\.html$", parsed.path, re.I):
            errors.append(f"non-canonical URL format: {url}")
            continue
        if require_lastmod and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod):
            errors.append(f"missing/invalid lastmod for {url}: {lastmod!r}")
        source = route_file(url)
        if source is None:
            errors.append(f"sitemap URL has no matching static route: {url}")
            continue
        parser = HeadParser()
        parser.feed(source.read_text(encoding="utf-8", errors="ignore"))
        if len(parser.canonicals) != 1:
            errors.append(f"expected exactly one canonical tag for {url}; found {len(parser.canonicals)} in {source.relative_to(ROOT)}")
        elif parser.canonicals[0] != url:
            errors.append(f"canonical mismatch for {url}: {parser.canonicals[0]} ({source.relative_to(ROOT)})")
        if any("noindex" in value for value in parser.robots):
            errors.append(f"noindex route included in sitemap: {url}")
    if main_urls is not None:
        for url, _ in entries:
            if url not in main_urls:
                errors.append(f"news sitemap URL missing from main sitemap: {url}")
    return urls, errors

def main():
    main_entries = read_sitemap(SITEMAP)
    main_urls = [url for url, _ in main_entries]
    _, errors = validate_sitemap(SITEMAP)
    if not main_urls:
        errors.append("sitemap.xml contains no URLs")
    if NEWS_SITEMAP.is_file():
        _, news_errors = validate_sitemap(NEWS_SITEMAP, set(main_urls), require_lastmod=False)
        errors.extend(news_errors)
    if errors:
        print("SITEMAP VALIDATION FAILED:")
        for error in errors[:100]:
            print(" - " + error)
        if len(errors) > 100:
            print(f" - ... and {len(errors)-100} additional errors")
        raise SystemExit(1)
    print(f"SITEMAP VALIDATION PASSED: {len(main_urls)} unique URLs; routes exist, canonicals match, and no noindex pages are listed.")

if __name__ == "__main__":
    main()
