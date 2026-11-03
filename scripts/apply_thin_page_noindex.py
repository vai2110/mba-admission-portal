#!/usr/bin/env python3
"""Mark very thin public root pages noindex,follow until substantive content exists."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"
EXCLUDED = {"404.html", "index.html", "college-guides.html", "colleges.html",
            "top-mba-colleges-in-india.html", "mba-colleges-by-exam.html",
            "exams.html", "privacy.html", "terms.html", "methodology.html"}
class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0
    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg", "template"}:
            self.skip += 1
    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg", "template"} and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def tag_attrs(tag):
    return {key.lower(): value for key, _, value in re.findall(
        r"""([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(['"])(.*?)\2""", tag, re.I | re.S
    )}

redirect_sources = set()
config = ROOT / "vercel.json"
if config.exists():
    try:
        redirects = json.loads(config.read_text(encoding="utf-8")).get("redirects", [])
        for rule in redirects:
            source = rule.get("source", "")
            destination = rule.get("destination", "")
            if source.startswith("/") and ":" not in source:
                clean = source.rstrip("/")
                if clean.endswith(".html"):
                    clean = clean[:-5]
                if clean.lstrip("/") != destination.rstrip("/").lstrip("/"):
                    redirect_sources.add(clean.lstrip("/"))
    except Exception:
        pass

rows = []
changed = 0
for path in sorted(ROOT.glob("*.html")):
    if path.name in EXCLUDED or path.stem in redirect_sources:
        continue
    html = path.read_text(encoding="utf-8", errors="replace")
    parser = VisibleText()
    parser.feed(re.sub(r"<!--.*?-->", " ", html, flags=re.S))
    words = len(re.sub(r"\s+", " ", " ".join(parser.parts)).strip().split())
    if words >= 400:
        continue
    title_match = re.search(r"<title\b[^>]*>(.*?)</title\s*>", html, re.I | re.S)
    title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else ""
    noindex = False
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I | re.S):
        attrs = tag_attrs(tag)
        if attrs.get("name", "").lower() == "robots" and "noindex" in attrs.get("content", "").lower():
            noindex = True
            break
    action = "already noindex,follow" if noindex else "set noindex,follow"
    if not noindex:
        robots = '<meta name="robots" content="noindex,follow">'
        if re.search(r"</head\s*>", html, re.I):
            html = re.sub(r"</head\s*>", robots + "\n</head>", html, count=1, flags=re.I)
        else:
            html = robots + html
        path.write_text(html, encoding="utf-8")
        changed += 1
    rows.append((path.stem, words, title, action))

report = [
    "# Thin-page review",
    "",
    "Pages below 400 visible words are set to noindex,follow until they are merged into a parent page or expanded with verified, unique information.",
    "No page content is deleted. Redirects are not created by this script.",
    "",
    f"- Thin pages reviewed: {len(rows)}",
    f"- New noindex directives added: {changed}",
    "",
    "| URL | Visible word count | Title | Decision |",
    "|---|---:|---|---|",
]
for slug, words, title, action in rows:
    safe_title = (title or "").replace("|", "\\|").replace("\n", " ")
    report.append(f"| /{slug} | {words} | {safe_title} | {action} |")
out = ROOT / "seo-audit" / "thin-page-review.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(report) + "\n", encoding="utf-8")
print(f"THIN PAGE REVIEW: reviewed={len(rows)}, newly_noindexed={changed}")
