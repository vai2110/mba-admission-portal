from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from html.parser import HTMLParser

BASE_URL = "https://collegedecoded.in"

ROOT = Path(__file__).resolve().parents[1]

# Internal/test pages that must never be included in the public sitemap.
EXCLUDED_PATHS = {
    "college-page-audit-dashboard.html",
    "content-audit.html",
    "github-direct-edit-test.html",
    "irma-deploy-trigger.html",
    "github-direct-edit-test.html",
    # Legacy dynamic IIM Ahmedabad route; canonical entity URL is /iim-ahmedabad.
    "college.html",
}

# URL -> latest source modification date.
url_dates = {}
url_signatures = {}

# Sitemap inclusion is deliberately stricter than indexability. Pages that are
# technically crawlable but contain very little main content should be improved
# before being advertised as priority URLs in the sitemap. This is not a
# Google-required word-count rule; it is an editorial quality safeguard.
MIN_SITEMAP_WORDS = 300

class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip += 1
    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def visible_word_count(html):
    parser = _TextParser()
    parser.feed(html)
    return len(re.sub(r"\\s+", " ", " ".join(parser.parts)).strip().split())


def file_lastmod(path: Path) -> str:
    """Return the latest Git commit date for a file, with mtime fallback."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        value = result.stdout.strip()
        if value:
            return value[:10]
    except Exception:
        pass

    try:
        return datetime.fromtimestamp(
            path.stat().st_mtime, tz=timezone.utc
        ).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


# Find all HTML pages in the repository.
for html_file in ROOT.rglob("*.html"):

    # Ignore technical/system folders.
    if any(part in {".git", "node_modules", ".github"} for part in html_file.parts):
        continue

    # Ignore known internal/test pages.
    if html_file.name.lower() in EXCLUDED_PATHS:
        continue

    try:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    # Skip pages explicitly marked noindex.
    if re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
        content,
        re.IGNORECASE,
    ):
        continue

    # Do not put extremely thin pages in the sitemap. They remain live and
    # indexable so they can be improved, but the sitemap should represent the
    # site's strongest, most useful URLs rather than every HTML file.
    if visible_word_count(content) < MIN_SITEMAP_WORDS:
        continue

    # Look for canonical URL.
    canonical_match = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        content,
        re.IGNORECASE,
    )

    if not canonical_match:
        canonical_match = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
            content,
            re.IGNORECASE,
        )

    if canonical_match:
        url = canonical_match.group(1).strip()

        # Only include CollegeDecoded canonical URLs.
        if url == BASE_URL or url.startswith(BASE_URL + "/"):
            url = url.rstrip("/") if url != BASE_URL else BASE_URL
        else:
            continue

    else:
        # Fallback: convert HTML filename to clean URL.
        relative = html_file.relative_to(ROOT)

        if relative.name.lower() == "index.html":
            url = BASE_URL + "/"
        else:
            path_without_extension = relative.with_suffix("")
            url = BASE_URL + "/" + str(path_without_extension).replace("\\", "/")

    # Use the page's canonical URL when one is declared.
    # This prevents legacy /overview and other implementation filenames from
    # leaking into the sitemap when the page canonicals to a clean URL.
    if canonical_match:
        canonical_url = canonical_match.group(1).strip()
        if canonical_url == BASE_URL:
            url = BASE_URL
        elif canonical_url.startswith(BASE_URL + "/"):
            url = canonical_url.rstrip("/")
        else:
            continue
    else:
        relative = html_file.relative_to(ROOT)
        if relative.name.lower() == "index.html":
            url = BASE_URL
        else:
            url = BASE_URL + "/" + str(relative.with_suffix("")).replace("\\", "/")

    lastmod = file_lastmod(html_file)
    url_dates[url] = max(url_dates.get(url, ""), lastmod)

# Sort URLs for a stable sitemap.
urls = sorted(url_dates)

# Build XML.
xml_lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
]

for url in urls:
    xml_lines.extend(
        [
            "  <url>",
            f"    <loc>{escape(url)}</loc>",
            f"    <lastmod>{escape(url_dates[url])}</lastmod>",
            "  </url>",
        ]
    )

xml_lines.append("</urlset>")

# Write sitemap.
sitemap_path = ROOT / "sitemap.xml"
sitemap_path.write_text(
    "\n".join(xml_lines) + "\n",
    encoding="utf-8",
)

print(f"Sitemap generated successfully with {len(urls)} URLs (excluding noindex and pages under {MIN_SITEMAP_WORDS} visible words) and lastmod dates.")
