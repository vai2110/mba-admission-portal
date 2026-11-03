#!/usr/bin/env python3
"""Generate a source-derived URL inventory for the CollegeDecoded static site."""
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"
OUT = ROOT / "seo-audit" / "inventory.md"
EXCLUDED = {"404.html", "content-audit.html", "college-page-audit-dashboard.html",
            "github-direct-edit-test.html", "irma-deploy-trigger.html"}

# Explicitly supplied duplicate clusters. Keep candidate selection separate from
# redirects: the inventory identifies clusters but does not choose winners.
CLUSTERS = {
    "chitkara-overview": ["chitkara-university", "chitkara-university-punjab"],
    "chitkara-admission": ["chitkara-university-admission", "chitkara-university-admission-2026"],
    "chitkara-btech": ["chitkara-university-btech", "chitkara-university-btech-2026"],
    "chitkara-bba-bcom": ["chitkara-university-bba-bcom", "chitkara-university-bba-bcom-2026"],
    "chitkara-mba": ["chitkara-university-mba", "chitkara-university-mba-2026"],
    "chitkara-placements": ["chitkara-university-placements", "chitkara-university-placements-2026"],
    "chitkara-hostel": ["chitkara-university-hostel", "chitkara-university-hostel-campus"],
    "chitkara-fees": ["chitkara-university-fees", "chitkara-university-courses-fees-2026"],
    "dms-nit-trichy-overview": ["dms-nit-trichy", "department-management-studies-nit-trichy"],
    "dms-nit-trichy-mba": ["dms-nit-trichy-mba", "department-management-studies-nit-trichy-mba"],
    "dms-nit-trichy-placements": ["dms-nit-trichy-placements", "department-management-studies-nit-trichy-placements"],
    "iit-roorkee-executive-mba": ["iit-roorkee-executive-mba", "indian-institute-of-technology-roorkee-executive-mba"],
    "iit-roorkee-placements": ["iit-roorkee-placements", "indian-institute-of-technology-roorkee-placements"],
    "jaipuria-noida": ["jaipuria-noida", "jaipuria-institute-management-noida", "jaipuria-noida-pgdm"],
    "iima-pgpx": ["iim-ahmedabad-pgpx", "iim-ahmedabad-mba-pgpx"],
    "ibs-hyderabad": ["ibs-hyderabad", "icfai-university-hyderabad-mba"],
    "tsm-hostel": ["tsm-campus-hostel", "tsm-campus-hostel-life"],
    "welingkar-programmes": ["welingkar-mumbai-programmes", "welingkar-mumbai-programmes-note"],
    "jmi-management": ["jmi", "jamia-millia-islamia-mba", "jmi-management-studies"],
    "exam-hub": ["exams", "mba-colleges-by-exam"],
}

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

def attrs(tag, name):
    m = re.search(r"<" + tag + r"\b[^>]*\b" + name + r"\s*=\s*(['""])(.*?)\1", tag, re.I | re.S)
    return m.group(2).strip() if m else ""

def meta_description(html):
    for m in re.finditer(r"<meta\b[^>]*>", html, re.I | re.S):
        tag = m.group(0)
        if re.search(r"\bname\s*=\s*['""]description['""]", tag, re.I):
            return attrs(tag, "content")
    return ""

def canonical(html, fallback):
    for m in re.finditer(r"<link\b[^>]*>", html, re.I | re.S):
        tag = m.group(0)
        if re.search(r"\brel\s*=\s*['""][^'""]*canonical[^'""]*['""]", tag, re.I):
            value = attrs(tag, "href")
            if value:
                return value
    return BASE + ("/" + fallback if fallback else "/")

def route_key(href, source):
    href = unquote((href or "").strip())
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    p = urlparse(href)
    if p.scheme or p.netloc:
        if p.netloc.lower() not in {"collegedecoded.in", "www.collegedecoded.in"}:
            return None
        href = p.path
    else:
        href = p.path
    if not href or href == "/":
        return "index.html"
    href = href.split("?", 1)[0].split("#", 1)[0].lstrip("/")
    if href.endswith("/"):
        href += "index.html"
    if not href.endswith(".html"):
        href += ".html"
    return href

def safe_cell(value):
    return str(value or "").replace("|", r"\|").replace("\n", " ").replace("\r", " ").strip()

files = sorted(p for p in ROOT.rglob("*.html")
               if not any(x in {".git", "node_modules", ".github", ".vercel"} for x in p.parts)
               and p.name.lower() not in EXCLUDED)
by_route = {}
pages = []
incoming = defaultdict(int)
for path in files:
    rel = path.relative_to(ROOT).as_posix()
    html = path.read_text(encoding="utf-8", errors="replace")
    parser = VisibleText()
    parser.feed(re.sub(r"<!--.*?-->", " ", html, flags=re.S))
    words = len(re.sub(r"\s+", " ", " ".join(parser.parts)).strip().split())
    title_match = re.search(r"<title\b[^>]*>(.*?)</title\s*>", html, re.I | re.S)
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title_match.group(1))).strip() if title_match else ""
    slug = "" if rel == "index.html" else rel[:-5]
    url = canonical(html, slug)
    if url.endswith(".html"):
        url = url[:-5]
    pages.append({"file": rel, "url": url, "words": words, "title": title,
                  "description": meta_description(html), "canonical": canonical(html, slug),
                  "html": html})
    by_route[rel] = pages[-1]

for page in pages:
    for m in re.finditer(r"<a\b[^>]*\bhref\s*=\s*(['""])(.*?)\1", page["html"], re.I | re.S):
        target = route_key(m.group(2), page["file"])
        if target and target in by_route and target != page["file"]:
            incoming[target] += 1

sitemap_urls = set()
sitemap = ROOT / "sitemap.xml"
if sitemap.exists():
    try:
        tree = ET.parse(sitemap)
        sitemap_urls = {n.text.strip().rstrip("/") if n.text and n.text.strip() != BASE + "/" else (n.text.strip() if n.text else "")
                        for n in tree.findall(".//{*}loc")}
    except ET.ParseError:
        pass

cluster_by_slug = {}
for cluster_id, slugs in CLUSTERS.items():
    for slug in slugs:
        cluster_by_slug[slug + ".html"] = cluster_id
# Detect year-suffixed twins only when the evergreen counterpart exists.
for page in pages:
    name = page["file"]
    m = re.match(r"^(.*)-20\d{2}\.html$", name)
    if m and m.group(1) + ".html" in by_route:
        cluster_by_slug.setdefault(name, "year-twin:" + m.group(1))

rows = []
for page in pages:
    canonical_url = page["canonical"].rstrip("/")
    if page["canonical"] == BASE + "/":
        canonical_url = BASE + "/"
    in_sitemap = canonical_url in sitemap_urls or canonical_url.rstrip("/") in sitemap_urls
    cluster = cluster_by_slug.get(page["file"], "")
    rows.append("| " + " | ".join([
        safe_cell(page["url"]), str(page["words"]), safe_cell(page["title"]),
        safe_cell(page["description"]), safe_cell(page["canonical"]),
        "y" if in_sitemap else "n", str(incoming[page["file"]]), safe_cell(cluster)
    ]) + " |")

OUT.parent.mkdir(parents=True, exist_ok=True)
header = [
    "# CollegeDecoded URL inventory",
    "",
    "Generated from repository HTML, canonical tags, sitemap.xml and static internal anchors during the Vercel build.",
    "Inbound counts are anchor occurrences in repository HTML, not Googlebot crawl counts. Cluster IDs identify candidates only; they do not approve a redirect or canonical winner.",
    "",
    f"- Inventory date: 2026-11-03",
    f"- HTML files inventoried: {len(pages)}",
    f"- URLs in sitemap.xml: {len(sitemap_urls)}",
    f"- Pages with zero inbound internal anchors: {sum(incoming[p['file']] == 0 for p in pages)}",
    "",
    "| URL | Word count | Title | Meta description | Canonical | In sitemap (y/n) | Inbound internal links | Duplicate-cluster ID |",
    "|---|---:|---|---|---|:---:|---:|---|",
]
OUT.write_text("\n".join(header + rows) + "\n", encoding="utf-8")

# Human-reviewable duplicate recommendations. These are not redirects: the
# build never removes pages or changes routes based on a similarity guess.
WINNERS = {
    "chitkara-overview": "chitkara-university-punjab",
    "chitkara-admission": "chitkara-university-admission",
    "chitkara-btech": "chitkara-university-btech",
    "chitkara-bba-bcom": "chitkara-university-bba-bcom",
    "chitkara-mba": "chitkara-university-mba",
    "chitkara-placements": "chitkara-university-placements",
    "chitkara-hostel": "chitkara-university-hostel",
    "chitkara-fees": "chitkara-university-fees",
    "dms-nit-trichy-overview": "dms-nit-trichy",
    "dms-nit-trichy-mba": "dms-nit-trichy-mba",
    "dms-nit-trichy-placements": "dms-nit-trichy-placements",
    "iit-roorkee-executive-mba": "iit-roorkee-executive-mba",
    "iit-roorkee-placements": "iit-roorkee-placements",
    "jaipuria-noida": "jaipuria-noida",
    "iima-pgpx": "iim-ahmedabad-pgpx",
    "ibs-hyderabad": "ibs-hyderabad",
    "tsm-hostel": "tsm-campus-hostel",
}
KEEP_SEPARATE = {
    "welingkar-programmes": "Different intent: programme catalogue versus career-fit decision guide.",
    "jmi-management": "Different scope: university overview, MBA course and department/management studies.",
    "exam-hub": "Different intent: exam information hub versus colleges accepting an exam.",
}
page_by_file = {p["file"]: p for p in pages}
review_lines = [
    "# Duplicate-cluster review",
    "",
    "Candidate winners are recommendations for manual review. No redirect is added by this report.",
    "Before redirecting, merge unique sections and verify conflicting figures against official source records.",
    "",
    "| Cluster ID | Candidate URLs | Candidate word counts | Recommended winner / decision |",
    "|---|---|---:|---|",
]
for cluster_id, slugs in CLUSTERS.items():
    present = [slug for slug in slugs if slug + ".html" in page_by_file]
    if not present:
        continue
    details = []
    counts = []
    for slug in present:
        page = page_by_file[slug + ".html"]
        details.append(f"/{slug}")
        counts.append(f"{slug}: {page['words']}")
    if cluster_id in KEEP_SEPARATE:
        decision = "KEEP SEPARATE: " + KEEP_SEPARATE[cluster_id]
    elif cluster_id in WINNERS:
        decision = f"/{WINNERS[cluster_id]} (merge unique content before redirect)"
    else:
        decision = "Needs manual review"
    review_lines.append("| " + " | ".join([
        safe_cell(cluster_id), safe_cell("; ".join(details)),
        safe_cell("; ".join(counts)), safe_cell(decision)
    ]) + " |")

(ROOT / "seo-audit" / "duplicate-review.md").write_text(
    "\n".join(review_lines) + "\n", encoding="utf-8"
)
print(f"SEO inventory written: {OUT.relative_to(ROOT)} ({len(pages)} HTML files).")
print(f"Duplicate review written: seo-audit/duplicate-review.md ({len(CLUSTERS)} supplied clusters).")
