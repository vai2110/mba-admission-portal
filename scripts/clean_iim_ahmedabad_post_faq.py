#!/usr/bin/env python3
"""Remove generated post-FAQ blocks from every IIM Ahmedabad page."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE_RE = re.compile(r"iim-ahmedabad(?:-[a-z0-9-]+)?\.html$", re.I)

PATTERNS = [
    re.compile(
        r'<nav\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bseo-cluster-links\b[^"\']*["\'])[^>]*>.*?</nav>',
        re.I | re.S,
    ),
    re.compile(
        r'<!--\s*COLLEGEDECODED-RELATED-NEWS:START\s*-->.*?<!--\s*COLLEGEDECODED-RELATED-NEWS:END\s*-->',
        re.I | re.S,
    ),
    re.compile(
        r'<section\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcd-related-news\b[^"\']*["\'])[^>]*>.*?</section>',
        re.I | re.S,
    ),
    re.compile(
        r'<style\b(?=[^>]*\bid\s*=\s*["\']seo-cluster-links-style["\'])[^>]*>.*?</style>',
        re.I | re.S,
    ),
]

def main():
    changed = []
    # Clean both source files and clean-URL copies such as
    # /iim-ahmedabad/index.html and /iim-ahmedabad-mba-pgpx/index.html.
    for page in ROOT.rglob("*.html"):
        if any(part.startswith(".") or part in {"node_modules", ".vercel"} for part in page.relative_to(ROOT).parts):
            continue
        is_root_page = PAGE_RE.fullmatch(page.name) is not None
        is_clean_url_copy = (
            page.name.lower() == "index.html"
            and PAGE_RE.fullmatch(page.parent.name + ".html") is not None
        )
        if not (is_root_page or is_clean_url_copy):
            continue
        original = page.read_text(encoding="utf-8")
        cleaned = original
        for pattern in PATTERNS:
            cleaned = pattern.sub("", cleaned)
        if cleaned != original:
            page.write_text(cleaned, encoding="utf-8")
            changed.append(page.name)
    print(f"IIM Ahmedabad post-FAQ cleanup: {len(changed)} page(s) cleaned; no related-link/news footer blocks are allowed.")
    for name in changed:
        print(name)

if __name__ == "__main__":
    main()
