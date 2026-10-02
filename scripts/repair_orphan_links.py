import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    "404.html", "content-audit.html", "college-page-audit-dashboard.html",
    "github-direct-edit-test.html", "irma-deploy-trigger.html"
}
PROTECTED = {"iim-ahmedabad.html", "sibm-pune.html"}

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self.hrefs.append(v)
                    break

def hrefs(html):
    p = Parser()
    p.feed(html)
    p.close()
    return p.hrefs

def target(href):
    href = href.strip()
    if not href or href.startswith(("#", "http://", "https://", "mailto:", "tel:", "javascript:", "data:")):
        return None
    path = (urlsplit(href).path or "/").rstrip("/") or "/"
    raw = path.lstrip("/") if path.startswith("/") else path
    if not raw:
        return "index.html"
    for c in (raw, raw + ".html" if not raw.endswith(".html") else raw[:-5], raw + "/index.html"):
        if (ROOT / c).is_file():
            return Path(c).as_posix()
    return None

def normalize_existing_links(html):
    return {t for h in hrefs(html) if (t := target(h))}

def label(name):
    return Path(name).stem.replace("-", " ").replace("_", " ").title()

def overview_for(page, page_set):
    stem = Path(page).stem
    if stem.endswith("-placements"):
        base = stem[:-11] + ".html"
        return base if base in page_set else None

    # Find the longest existing overview prefix.
    parts = stem.split("-")
    for i in range(len(parts) - 1, 0, -1):
        candidate = "-".join(parts[:i]) + ".html"
        if candidate in page_set and not candidate.endswith("-placements.html"):
            return candidate
    return None

def best_source(page, page_set):
    stem = Path(page).stem
    overview = overview_for(page, page_set)
    if overview and overview != page:
        if stem.endswith("-placements"):
            return overview
        # Programme/content page -> overview is the natural parent.
        return overview

    # An orphan overview should be linked from its placement page where available.
    placement = stem + "-placements.html"
    if placement in page_set and placement != page:
        return placement

    # Otherwise use the closest same-prefix sibling.
    siblings = sorted(
        p for p in page_set
        if p != page and p.startswith(stem + "-") and p not in EXCLUDED
    )
    if siblings:
        return siblings[0]

    # Safe contextual hub fallback for standalone valid pages.
    # Never fall back to the homepage: the hub must be topically relevant.
    if page in {"top-mba-colleges-in-india.html", "mba-colleges-by-location.html", "colleges.html"}:
        return None

    hub_candidates = []
    if page.endswith("-placements.html") or any(
        token in stem for token in (
            "-mba", "-pgdm", "-pgp", "-bba", "-bca", "-bcom",
            "-btech", "-mca", "-mtech", "-executive", "-ipm", "-mms"
        )
    ):
        hub_candidates = ["colleges.html", "top-mba-colleges-in-india.html"]

    if not hub_candidates:
        hub_candidates = ["colleges.html"]

    for hub in hub_candidates:
        if hub in page_set and hub != page:
            return hub

    return None

def add_grouped_links(source, destinations):
    path = ROOT / source
    html = path.read_text(encoding="utf-8")
    existing = normalize_existing_links(html)
    missing = [d for d in destinations if d not in existing and d != source]
    if not missing:
        return False

    links = " · ".join(
        f'<a href="/{d[:-5]}">{label(d)}</a>' for d in sorted(missing)
    )
    block = (
        '<nav class="seo-related-link" aria-label="Related pages">'
        '<strong>Related pages</strong> ' + links + '</nav>'
    )

    # Replace only a previously generated block so repeated builds remain idempotent.
    html = re.sub(
        r'<nav\b[^>]*class=["\'][^"\']*\bseo-related-link\b[^"\']*["\'][^>]*>.*?</nav>',
        '',
        html,
        flags=re.I | re.S,
    )
    body = re.search(r"</body>", html, flags=re.I)
    if not body:
        return False

    html = html[:body.start()] + block + "\n" + html[body.start():]

    css = '''<style id="seo-related-link-style">
.seo-related-link{margin:18px 0;padding:10px 0;font-size:13px;line-height:1.7}
.seo-related-link strong{margin-right:8px;color:#173f82}
.seo-related-link a{color:#2563eb;font-weight:600;text-decoration:none}
.seo-related-link a:hover{text-decoration:underline}
</style>'''
    if "seo-related-link-style" not in html:
        head = re.search(r"</head>", html, flags=re.I)
        if head:
            html = html[:head.start()] + css + "\n" + html[head.start():]

    path.write_text(html, encoding="utf-8")
    return True

def main():
    pages = sorted(
        p.name for p in ROOT.glob("*.html")
        if p.name not in EXCLUDED
    )
    page_set = set(pages)

    incoming = Counter()
    for p in pages:
        for h in hrefs((ROOT / p).read_text(encoding="utf-8")):
            t = target(h)
            if t in page_set:
                incoming[t] += 1

    orphans = [
        p for p in pages
        if incoming[p] == 0 and p not in PROTECTED
    ]

    grouped = defaultdict(list)
    unresolved = []
    for orphan in orphans:
        source = best_source(orphan, page_set)
        if source:
            grouped[source].append(orphan)
        else:
            unresolved.append(orphan)

    changed = 0
    links_added = 0
    for source, destinations in sorted(grouped.items()):
        before = normalize_existing_links((ROOT / source).read_text(encoding="utf-8"))
        if add_grouped_links(source, destinations):
            changed += 1
            after = normalize_existing_links((ROOT / source).read_text(encoding="utf-8"))
            links_added += len(set(destinations) & (after - before))

    print(
        f"Orphan link repair: {links_added} links added across {changed} source pages; "
        f"{len(unresolved)} pages have no safe parent/sibling source."
    )
    for page in unresolved:
        print(f"- UNRESOLVED: {page}")

if __name__ == "__main__":
    main()
