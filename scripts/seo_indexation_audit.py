from pathlib import Path
from collections import defaultdict
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

def clean_for_signature(text):
    return re.sub(r"\s+", " ", text).strip().lower()

pages = []
signatures = defaultdict(list)

for path in ROOT.glob("*.html"):
    if path.name.lower() in EXCLUDED:
        continue

    html = path.read_text(encoding="utf-8", errors="ignore")
    text = extract_text(html)
    words = len(text.split())

    noindex = bool(re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
        html, re.I
    ))

    canonical = ""
    m = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        html, re.I
    )
    if not m:
        m = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
            html, re.I
        )
    if m:
        canonical = m.group(1).strip()

    signature = clean_for_signature(text)
    if signature:
        signatures[signature].append(path.name)

    if noindex:
        classification = "noindex"
    elif words < 300:
        classification = "review-thin"
    elif words < 600:
        classification = "review-depth"
    else:
        classification = "index-candidate"

    pages.append({
        "file": path.name,
        "words": words,
        "canonical": canonical,
        "noindex": noindex,
        "classification": classification,
    })

duplicates = []
for signature, files in signatures.items():
    if len(files) > 1:
        duplicates.append({
            "files": sorted(files),
            "word_count": len(signature.split()),
        })

summary = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "pages_scanned": len(pages),
    "index_candidates": sum(x["classification"] == "index-candidate" for x in pages),
    "review_depth": sum(x["classification"] == "review-depth" for x in pages),
    "review_thin": sum(x["classification"] == "review-thin" for x in pages),
    "existing_noindex": sum(x["classification"] == "noindex" for x in pages),
    "exact_duplicate_groups": len(duplicates),
}

OUTPUT.write_text(
    json.dumps({
        "summary": summary,
        "pages": sorted(pages, key=lambda x: (x["classification"], x["words"])),
        "exact_duplicates": duplicates,
    }, indent=2),
    encoding="utf-8",
)

print(json.dumps(summary, indent=2))
