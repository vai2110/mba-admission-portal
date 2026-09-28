from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, unquote
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "seo-indexation-audit.json"

EXCLUDED = {
    "college-page-audit-dashboard.html",
    "content-audit.html",
    "github-direct-edit-test.html",
    "irma-deploy-trigger.html",
}

class TextParser(HTMLParser):
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

def extract_text(html):
    parser = TextParser()
    parser.feed(html)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()

def canonical_from(html):
    m = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        html, re.I
    )
    if not m:
        m = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
            html, re.I
        )
    return m.group(1).strip() if m else ""

def page_family(name):
    n = name.lower()
    if "placements" in n:
        return "placement"
    if "fees" in n:
        return "fees"
    if "admission" in n:
        return "admission"
    if "cutoff" in n:
        return "cutoff"
    if "hostel" in n or "campus" in n:
        return "campus-hostel"
    if re.search(r"-(mba|bba|bca|btech|mca|mtech|mbbs|bcom|barch|bds)(-|\.|$)", n):
        return "programme"
    if re.search(r"-20\d{2}(?:\.|$)", n):
        return "year-specific"
    return "overview-or-hub"

def shingles(text, size=5):
    words = re.findall(r"[a-z0-9]+", text.lower())
    if len(words) < size:
        return set(words)
    return {" ".join(words[i:i+size]) for i in range(len(words)-size+1)}

pages = []
html_paths = {str(p.relative_to(ROOT)).replace('\\\\', '/'): p for p in ROOT.rglob('*.html') if not any(part in {'.git', 'node_modules', '.github'} for part in p.parts)}
for path in ROOT.rglob("*.html"):
    if any(part in {".git", "node_modules", ".github"} for part in path.parts):
        continue
    if path.name.lower() in EXCLUDED:
        continue

    html = path.read_text(encoding="utf-8", errors="ignore")
    text = extract_text(html)
    words = len(text.split())

    noindex = bool(re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
        html, re.I
    ))

    if noindex:
        classification = "noindex"
    elif words < 300:
        classification = "review-thin"
    elif words < 600:
        classification = "review-depth"
    else:
        classification = "index-candidate"

    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    pages.append({
        "file": rel,
        "words": words,
        "canonical": canonical_from(html),
        "canonical_missing": not bool(canonical_from(html)),
        "noindex": noindex,
        "family": page_family(path.name),
        "classification": classification,
        "_shingles": shingles(text),
    })


# Build a lightweight internal-link graph from static HTML anchors.
# This is report-only: it never rewrites links or indexation directives.
def resolve_internal_target(source_path, href):
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    href = unquote(href.strip())
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        if parsed.netloc and parsed.netloc.lower() not in {"collegedecoded.in", "www.collegedecoded.in"}:
            return None
        target = parsed.path
    else:
        target = href.split("#", 1)[0].split("?", 1)[0]
    if not target:
        target = "/index.html"
    if target.startswith("/"):
        rel = target.lstrip("/")
    else:
        rel = str((Path(source_path).parent / target).as_posix())
    rel = re.sub(r"/+", "/", rel).lstrip("./")
    if rel.endswith("/"):
        rel += "index.html"
    if rel in html_paths:
        return rel
    if rel.endswith(".html") and rel[:-5] + ".html" in html_paths:
        return rel
    clean = rel[:-5] if rel.endswith(".html") else rel
    if clean + ".html" in html_paths:
        return clean + ".html"
    return None

incoming = defaultdict(int)
outgoing = {}
anchor_parser_re = re.compile(r'<a\\b[^>]*href=["\\']([^"\\']+)["\\']', re.I)

for page in pages:
    source = page["file"]
    html = (ROOT / source).read_text(encoding="utf-8", errors="ignore")
    targets = []
    for href in anchor_parser_re.findall(html):
        target = resolve_internal_target(source, href)
        if target and target != source:
            targets.append(target)
            incoming[target] += 1
    outgoing[source] = len(set(targets))

for page in pages:
    page["internal_links_out"] = outgoing.get(page["file"], 0)
    page["internal_links_in"] = incoming.get(page["file"], 0)
    page["orphan_candidate"] = (
        not page["noindex"]
        and page["internal_links_in"] == 0
        and page["file"] not in {"index.html", "404.html"}
    )

# Near-duplicate detection is deliberately report-only. It never changes robots/canonical.
near_duplicates = []
for i, left in enumerate(pages):
    if left["noindex"] or left["words"] < 150:
        continue
    for right in pages[i+1:]:
        if right["noindex"] or right["words"] < 150:
            continue
        if left["family"] != right["family"]:
            continue
        a, b = left["_shingles"], right["_shingles"]
        if not a or not b:
            continue
        similarity = len(a & b) / len(a | b)
        if similarity >= 0.72:
            near_duplicates.append({
                "files": [left["file"], right["file"]],
                "families": [left["family"], right["family"]],
                "similarity": round(similarity, 3),
                "words": [left["words"], right["words"]],
            })

exact_duplicates = []
signatures = defaultdict(list)
for page in pages:
    if page["noindex"]:
        continue
    signature = re.sub(r"\s+", " ", page["file"] + " " + str(page["words"])).strip()
    # Exact duplicate content is handled by the sitemap generator. This report
    # intentionally records near-duplicates without duplicating that logic.

summary = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "pages_scanned": len(pages),
    "index_candidates": sum(x["classification"] == "index-candidate" for x in pages),
    "review_depth": sum(x["classification"] == "review-depth" for x in pages),
    "review_thin": sum(x["classification"] == "review-thin" for x in pages),
    "existing_noindex": sum(x["classification"] == "noindex" for x in pages),
    "canonical_missing": sum(x["canonical_missing"] for x in pages),
    "near_duplicate_pairs": len(near_duplicates),
    "orphan_candidates": sum(x["orphan_candidate"] for x in pages),
    "low_internal_link_pages": sum((not x["noindex"]) and x["internal_links_in"] <= 1 and x["file"] not in {"index.html", "404.html"} for x in pages),
    "note": "Thin and near-duplicate findings are review-only; no automatic noindex is applied.",
}

for page in pages:
    page.pop("_shingles", None)

OUTPUT.write_text(
    json.dumps({
        "summary": summary,
        "pages": sorted(pages, key=lambda x: (x["classification"], x["words"])),
        "near_duplicates": near_duplicates,
        "exact_duplicates": exact_duplicates,
    }, indent=2),
    encoding="utf-8",
)

print(json.dumps(summary, indent=2))
