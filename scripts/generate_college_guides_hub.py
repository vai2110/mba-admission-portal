#!/usr/bin/env python3
"""Build a clean, crawlable hub for public CollegeDecoded college/course pages.

The build only lists pages with at least 300 visible words; this is a review threshold, not a Google rule.

This repairs weak discovery paths without changing canonical or robots directives.
Noindex pages and technical/test pages are deliberately excluded.
"""
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"
HUB_FILE = ROOT / "college-guides.html"
EXCLUDED = {
    "404.html", "college-page-audit-dashboard.html", "content-audit.html",
    "github-direct-edit-test.html", "irma-deploy-trigger.html", "college.html",
}
LINK_CLASS = "all-college-guides-link"

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

def visible_text(html):
    # Remove script/style content before extracting visible words.
    html = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1\s*>", " ", html, flags=re.I | re.S)
    p = TextParser()
    p.feed(html)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()

def canonical_for(html, path):
    m = re.search(r'<link\b[^>]*\brel=["\']canonical["\'][^>]*\bhref=["\']([^"\']+)["\']', html, re.I)
    if not m:
        m = re.search(r'<link\b[^>]*\bhref=["\']([^"\']+)["\'][^>]*\brel=["\']canonical["\']', html, re.I)
    if m:
        url = m.group(1).strip()
    else:
        url = BASE + ("" if path.name == "index.html" else "/" + path.stem)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "collegedecoded.in" or parsed.query or parsed.fragment:
        return None
    clean_path = parsed.path.rstrip("/")
    if clean_path.lower().endswith(".html"):
        return None
    return BASE + clean_path if clean_path else BASE

def title_for(html, path):
    m = re.search(r"<title\b[^>]*>(.*?)</title\s*>", html, re.I | re.S)
    if m:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    return path.stem.replace("-", " ").replace("_", " ").title()

def is_noindex(html):
    return bool(re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\'][^"\']*noindex', html, re.I))

def escape(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def main():
    pages = {}
    for path in sorted(ROOT.glob("*.html")):
        if path.name in EXCLUDED or path.name == HUB_FILE.name:
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        if is_noindex(html):
            continue
        canonical = canonical_for(html, path)
        if not canonical:
            continue
        # Do not promote thin pages into a giant discovery directory; they remain live for editorial review.
        words = len(visible_text(html).split())
        if words < 300:
            continue
        pages[canonical] = {"path": path, "title": title_for(html, path), "words": words}

    grouped = defaultdict(list)
    for url, item in pages.items():
        title = item["title"] or item["path"].stem
        first = re.sub(r"^https://collegedecoded\.in/?", "", url).split("/", 1)[0]
        # Group by first meaningful title character for a predictable, light-weight directory.
        letter = re.sub(r"[^A-Za-z0-9]", "", title[:1]).upper() or "#"
        grouped[letter].append((title, url))

    sections = []
    for letter in sorted(grouped):
        items = sorted(grouped[letter], key=lambda x: x[0].casefold())
        links = "".join(f'<li><a href="{escape(url.replace(BASE, "" ) or "/")}">{escape(title)}</a></li>' for title, url in items)
        sections.append(f'<section id="letter-{escape(letter)}"><h2>{escape(letter)}</h2><ul>{links}</ul></section>')

    hub = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All College &amp; Course Guides | CollegeDecoded</title>
<meta name="description" content="Browse CollegeDecoded's college, course, admission, fees, cutoff and placement guides in one searchable directory.">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="https://collegedecoded.in/college-guides">
<style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;font:16px/1.6 Arial,Helvetica,sans-serif;color:#172033;background:#f7f9fc}
header,main,footer{width:min(1120px,calc(100% - 32px));margin:auto}header{padding:32px 0 18px}h1{font-size:clamp(28px,4vw,40px);line-height:1.2;color:#102a72;margin:0 0 12px}header p{max-width:760px;color:#526174}
.quick{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}.quick a{padding:5px 10px;border:1px solid #d8e2f0;border-radius:18px;background:#fff;color:#2458d8;text-decoration:none}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px;padding-bottom:32px}section{background:#fff;border:1px solid #e0e7f0;border-radius:12px;padding:16px;min-width:0}h2{font-size:22px;color:#102a72;margin:0 0 10px}ul{margin:0;padding-left:19px}li{margin:5px 0;overflow-wrap:anywhere}a{color:#2458d8}footer{padding:16px 0 30px;color:#64748b;font-size:13px}
</style>
</head>
<body>
<header><h1>All College &amp; Course Guides</h1><p>Browse college profiles and dedicated guides for admissions, courses, fees, cutoffs, placements and campus information. Select a guide for the details relevant to that college or programme.</p>
<nav class="quick" aria-label="Jump to letter">""" + "".join(f'<a href="#letter-{escape(letter)}">{escape(letter)}</a>' for letter in sorted(grouped)) + """</nav></header>
<main>""" + "\n".join(sections) + """</main>
<footer>CollegeDecoded — college information and student guides.</footer>
<script src="/no-hash-navigation.js?v=20261010" defer></script>
</body></html>
"""
    HUB_FILE.write_text(hub, encoding="utf-8")

    # Keep the directory discoverable from the main landing pages without adding boilerplate
    # links to every article. The directory itself provides the crawlable links to its entries.
    injected = 0
    for filename in ("index.html", "colleges.html"):
        path = ROOT / filename
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'<a\b[^>]*href=["\']/college-guides["\']', html, re.I):
            continue
        link = '<nav class="all-college-guides-link" aria-label="College guide directory"><a href="/college-guides">Browse all college and course guides</a></nav>'
        style = '<style id="all-college-guides-link-style">.all-college-guides-link{margin:18px auto;padding:10px 16px;width:min(1120px,calc(100% - 32px));font-size:13px;border-top:1px solid #e5eaf2}.all-college-guides-link a{color:#2458d8;font-weight:600;text-decoration:none}.all-college-guides-link a:hover{text-decoration:underline}</style>'
        if "all-college-guides-link-style" not in html:
            head = re.search(r"</head\s*>", html, re.I)
            if head:
                html = html[:head.start()] + style + "\n" + html[head.start():]
        body = re.search(r"</body\s*>", html, re.I)
        if body:
            html = html[:body.start()] + link + "\n" + html[body.start():]
            path.write_text(html, encoding="utf-8")
            injected += 1
    # Provide crawlable HTML links to city pages; the location filters themselves are client-rendered.
    location_hub = ROOT / "mba-colleges-by-location.html"
    if location_hub.exists():
        location_html = location_hub.read_text(encoding="utf-8", errors="ignore")
        marker = 'class="crawlable-location-guides"'
        if marker not in location_html:
            cities = [
                ("mba-colleges-in-ahmedabad", "MBA colleges in Ahmedabad"),
                ("mba-colleges-in-bengaluru", "MBA colleges in Bengaluru"),
                ("mba-colleges-in-chennai", "MBA colleges in Chennai"),
                ("mba-colleges-in-delhi-ncr", "MBA colleges in Delhi NCR"),
                ("mba-colleges-in-hyderabad", "MBA colleges in Hyderabad"),
                ("mba-colleges-in-kolkata", "MBA colleges in Kolkata"),
                ("mba-colleges-in-mumbai", "MBA colleges in Mumbai"),
                ("mba-colleges-in-pune", "MBA colleges in Pune"),
            ]
            city_links = []
            for slug, label in cities:
                target = ROOT / (slug + ".html")
                if not target.is_file():
                    continue
                target_html = target.read_text(encoding="utf-8", errors="ignore")
                if is_noindex(target_html):
                    continue
                city_links.append(f'<li><a href="/{slug}">{escape(label)}</a></li>')
            if city_links:
                style = '<style id="crawlable-location-guides-style">.crawlable-location-guides{max-width:1120px;margin:24px auto;padding:20px 24px;border:1px solid #dbe5f2;border-radius:14px;background:#fff}.crawlable-location-guides h2{margin:0 0 8px;color:#102a72}.crawlable-location-guides p{margin:0 0 12px;color:#526174}.crawlable-location-guides ul{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px 20px;padding-left:20px}.crawlable-location-guides a{color:#2458d8;font-weight:600}</style>'
                section = '<section class="crawlable-location-guides" aria-labelledby="crawlable-location-guides-title"><h2 id="crawlable-location-guides-title">Explore MBA colleges by city</h2><p>Compare city-specific MBA college options, admissions, fees, entrance exams and placements.</p><ul>' + "".join(city_links) + '</ul></section>'
                head_pos = location_html.lower().find("</head>")
                if head_pos >= 0 and "crawlable-location-guides-style" not in location_html:
                    location_html = location_html[:head_pos] + style + "\n" + location_html[head_pos:]
                # Place the link block after the real footer, still inside the body.
                # A raw rfind("</body>") can match a literal in inline script/template text.
                footer_end = location_html.lower().rfind("</footer>")
                if footer_end >= 0:
                    insert_at = footer_end + len("</footer>")
                else:
                    insert_at = location_html.lower().find("</body>")
                if insert_at >= 0:
                    location_html = location_html[:insert_at] + "\n" + section + "\n" + location_html[insert_at:]
                    location_hub.write_text(location_html, encoding="utf-8")
                    print(f"Crawlable location links added: {len(city_links)} city pages.")
    print(f"College guide discovery hub generated: {len(pages)} substantive canonical public pages; directory links added to {injected} main landing pages.")

if __name__ == "__main__":
    main()
