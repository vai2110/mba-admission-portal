from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from html.parser import HTMLParser
from urllib.parse import urlparse
import json

BASE_URL = "https://collegedecoded.in"

ROOT = Path(__file__).resolve().parents[1]

def tag_attrs(tag_html):
    return {key.lower(): value for key, _, value in re.findall(
        r"""([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(['"])(.*?)\2""",
        tag_html, flags=re.I | re.S
    )}

def redirected_paths():
    config = ROOT / "vercel.json"
    if not config.exists():
        return set()
    try:
        rules = json.loads(config.read_text(encoding="utf-8")).get("redirects", [])
    except Exception:
        return set()
    paths = set()
    for rule in rules:
        source = rule.get("source", "")
        destination = rule.get("destination", "")
        if not source.startswith("/") or ":" in source:
            continue
        src = source.rstrip("/") or "/"
        dst = urlparse(destination).path.rstrip("/") or "/"
        if src.endswith(".html"):
            clean_src = src[:-5] or "/"
            if dst == clean_src:
                continue
            src = clean_src
        if src != dst:
            paths.add(src)
    return paths

REDIRECTED_PATHS = redirected_paths()

# Internal/test pages that must never be included in the public sitemap.
EXCLUDED_PATHS = {
    "college-page-audit-dashboard.html",
    "content-audit.html",
    "github-direct-edit-test.html",
    "irma-deploy-trigger.html",
    "github-direct-edit-test.html",
    # Legacy dynamic IIM Ahmedabad route; canonical entity URL is /iim-ahmedabad.
    "college.html",
    # Legacy .html alias is redirected by Vercel cleanUrls; never advertise it in sitemap.
    "iim-ahmedabad.html",
}

# URL -> latest source modification date.
url_dates = {}
url_signatures = {}

# Do not use a fixed word-count threshold to decide sitemap eligibility.
# Every public, canonical, indexable page may be included; thin pages should be
# improved editorially rather than silently omitted from the sitemap.

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
    return len(re.sub(r"\s+", " ", " ".join(parser.parts)).strip().split())


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

    # Skip pages explicitly marked noindex, regardless of attribute order.
    noindex = False
    for meta_tag in re.findall(r"<meta\b[^>]*>", content, flags=re.I | re.S):
        meta_attrs = tag_attrs(meta_tag)
        if meta_attrs.get("name", "").lower() == "robots" and "noindex" in meta_attrs.get("content", "").lower():
            noindex = True
            break
    if noindex:
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
        # Missing canonical pages must be repaired, not silently advertised.
        continue

    # Use the page's canonical URL when one is declared.
    # This prevents legacy /overview and other implementation filenames from
    # leaking into the sitemap when the page canonicals to a clean URL.
    if canonical_match:
        canonical_url = canonical_match.group(1).strip()
        if canonical_url == BASE_URL or canonical_url == BASE_URL + "/":
            # Preserve the exact homepage canonical URL. The homepage declares
            # https://collegedecoded.in/, so the sitemap must use that same URL.
            url = canonical_url
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

    # Keep only the source file that owns its canonical route. Nested CMS
    # copies and duplicate canonical files are excluded from the public sitemap.
    relative = html_file.relative_to(ROOT)
    if relative.name.lower() == "index.html":
        expected_path = "/" if relative.parent == Path(".") else "/" + relative.parent.as_posix()
    else:
        expected_path = "/" + relative.with_suffix("").as_posix()
    canonical_path = urlparse(url).path.rstrip("/") or "/"
    expected_clean = expected_path.rstrip("/") or "/"
    if canonical_path != expected_clean:
        continue
    if canonical_path in REDIRECTED_PATHS:
        continue

    # Never advertise a legacy .html URL in the sitemap, even if a stale canonical tag exists.
    if re.search(r"\.html(?:$|[?#])", url, re.IGNORECASE):
        continue

    # Keep only clean HTTPS URLs on the canonical origin, without query or fragment variants.
    if not url.startswith(BASE_URL) or "?" in url or "#" in url:
        continue

    lastmod = file_lastmod(html_file)
    url_dates[url] = max(url_dates.get(url, ""), lastmod)

# Explicitly include the IIM Ahmedabad clean canonical URL.
# Its only source file is the legacy .html filename, intentionally excluded
# above. Publish the canonical clean URL once, but never the legacy URL.
iima_source = ROOT / "iim-ahmedabad.html"
iima_url = BASE_URL + "/iim-ahmedabad"
if iima_source.is_file():
    try:
        iima_html = iima_source.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        iima_html = ""
    # The source page declares this exact clean canonical URL. Check both
    # supported quote styles and allow either attribute order without complex
    # quote-sensitive regexes in the build script.
    has_clean_canonical = (
        ('rel="canonical"' in iima_html.lower() or "rel='canonical'" in iima_html.lower())
        and iima_url.lower() in iima_html.lower()
    )
    is_indexable = "noindex" not in iima_html.lower()
    if has_clean_canonical and is_indexable:
        url_dates[iima_url] = max(url_dates.get(iima_url, ""), file_lastmod(iima_source))

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

print(f"Sitemap generated successfully with {len(urls)} canonical, indexable URLs and lastmod dates.")
