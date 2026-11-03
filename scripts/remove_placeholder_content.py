#!/usr/bin/env python3
"""Remove unsubstantiated placeholder discussion blocks and genuinely empty FAQ items."""
from pathlib import Path
from bs4 import BeautifulSoup
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "node_modules", ".github", ".vercel"}
PLACEHOLDER_PHRASES = (
    "decision themes, not fabricated student quotes",
    "not fabricated student quotes",
    "discussion themes, not official university claims",
    "these are decision themes",
)
counts = {"pages_scanned": 0, "placeholder_blocks_removed": 0,
          "discussion_sections_removed": 0, "empty_faq_items_removed": 0,
          "pages_changed": 0}

for path in sorted(ROOT.rglob("*.html")):
    if any(part in SKIP_PARTS for part in path.parts):
        continue
    counts["pages_scanned"] += 1
    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    changed = False
    removed_ids = set()

    # Remove explicit editorial placeholder sentences wherever they appear.
    for node in list(soup.find_all(["p", "div", "blockquote", "li"])):
        text = node.get_text(" ", strip=True).lower()
        if text and any(phrase in text for phrase in PLACEHOLDER_PHRASES):
            node.decompose()
            counts["placeholder_blocks_removed"] += 1
            changed = True

    # A Student Discussion section is retained only when it contains traceable
    # public discussion links or an actual quoted/source-attributed contribution.
    for heading in list(soup.find_all(["h2", "h3", "h4"])):
        label = re.sub(r"\s+", " ", heading.get_text(" ", strip=True)).strip().lower()
        if "student discussion" not in label:
            continue
        container = heading
        found_container = False
        for _ in range(6):
            if not container.parent:
                break
            container = container.parent
            classes = set(container.get("class") or [])
            if container.name == "section" or "main-section" in classes:
                found_container = True
                break
        if not found_container:
            continue
        source_links = container.find_all("a", href=re.compile(r"(reddit\.com|quora\.com|pagalguy\.com)", re.I))
        quotes = container.find_all(["blockquote", "q"])
        attributed = bool(re.search(r"\b(Reddit|Quora|student review|student report)\b", container.get_text(" ", strip=True), re.I))
        if source_links or quotes or attributed:
            continue
        section_id = container.get("id")
        if section_id:
            removed_ids.add(section_id)
        container.decompose()
        counts["discussion_sections_removed"] += 1
        changed = True

    # Remove only FAQ entries with no answer text. Hidden-but-populated answers
    # are preserved because they remain in the HTML source and page content.
    for item in list(soup.select(".faq-item, .accordion")):
        question = item.find(["h3", "h4", "summary"])
        if not question:
            continue
        answer_nodes = [node for node in item.find_all(["p", "div"])
                        if node is not item and node is not question and
                        not node.find(["h3", "h4", "summary"])]
        answer_text = " ".join(node.get_text(" ", strip=True) for node in answer_nodes).strip()
        if not answer_text:
            item.decompose()
            counts["empty_faq_items_removed"] += 1
            changed = True

    # Remove navigation anchors that point to discussion sections removed above.
    for section_id in removed_ids:
        for link in soup.find_all("a", href="#" + section_id):
            link.decompose()
            changed = True

    if changed:
        path.write_text(str(soup), encoding="utf-8")
        counts["pages_changed"] += 1

print("PLACEHOLDER CLEANUP: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
