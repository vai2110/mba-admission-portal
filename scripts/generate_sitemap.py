from pathlib import Path
import re
from xml.sax.saxutils import escape

BASE_URL = "https://collegedecoded.in"

ROOT = Path(__file__).resolve().parents[1]

urls = set()

# Find all HTML pages in the repository
for html_file in ROOT.rglob("*.html"):

    # Ignore technical/system folders
    if any(part in {".git", "node_modules", ".github"} for part in html_file.parts):
        continue

    try:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    # Skip pages explicitly marked noindex
    if re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
        content,
        re.IGNORECASE
    ):
        continue

    # Look for canonical URL
    canonical_match = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        content,
        re.IGNORECASE
    )

    if not canonical_match:
        canonical_match = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
            content,
            re.IGNORECASE
        )

    if canonical_match:
        url = canonical_match.group(1).strip()

        # Only include CollegeDecoded canonical URLs
        if url == BASE_URL or url.startswith(BASE_URL + "/"):
            urls.add(url.rstrip("/") if url != BASE_URL else BASE_URL)

    else:
        # Fallback: convert HTML filename to clean URL
        relative = html_file.relative_to(ROOT)

        if relative.name.lower() == "index.html":
            url = BASE_URL + "/"
        else:
            path_without_extension = relative.with_suffix("")
            url = BASE_URL + "/" + str(path_without_extension).replace("\\", "/")

        urls.add(url)


# Sort URLs for a stable sitemap
urls = sorted(urls)

# Build XML
xml_lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
]

for url in urls:
    xml_lines.append(f"  <url><loc>{escape(url)}</loc></url>")

xml_lines.append("</urlset>")

# Write sitemap
sitemap_path = ROOT / "sitemap.xml"
sitemap_path.write_text(
    "\n".join(xml_lines) + "\n",
    encoding="utf-8"
)

print(f"Sitemap generated successfully with {len(urls)} URLs.")
