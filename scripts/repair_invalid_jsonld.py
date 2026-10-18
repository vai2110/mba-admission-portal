#!/usr/bin/env python3
"""Repair leaked/malformed JSON-LD script markup without touching visible page content.

The SEO-Geo script has occasionally been inserted inside an unfinished <meta>
attribute. Browsers then render part of the JSON-LD above the hero. This repair
removes only that malformed meta/script fragment; valid JSON-LD blocks and all
page content/layout are preserved.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".vercel"}
MARKER = '<script data-mba-schema="seo-geo-aeo"'

def repair_schema_leaks(raw):
    changed = False
    while True:
        lower = raw.lower()
        pos = lower.find(MARKER)
        if pos < 0:
            break
        # If a tag opener is still active at the marker, the script was embedded
        # in an attribute (e.g. <meta content="web<script ...).
        last_open = lower.rfind("<", 0, pos)
        last_close = lower.rfind(">", 0, pos)
        if last_open < 0 or last_open < last_close:
            # This occurrence is in normal markup; inspect later occurrences.
            next_pos = lower.find(MARKER, pos + len(MARKER))
            if next_pos < 0:
                break
            # Temporarily skip this healthy marker while checking later ones.
            search_from = next_pos
            while search_from >= 0:
                op = lower.rfind("<", 0, search_from)
                cl = lower.rfind(">", 0, search_from)
                if op >= 0 and op > cl and lower.startswith("<meta", op):
                    pos = search_from
                    last_open = op
                    break
                search_from = lower.find(MARKER, search_from + len(MARKER))
            else:
                break
        else:
            last_open = lower.rfind("<meta", 0, pos)
            if last_open < 0 or last_open < last_close:
                break
        if not lower.startswith("<meta", last_open):
            break
        first_end = lower.find("</script>", pos)
        if first_end < 0:
            # Remove the broken tag through the end of the head if its script
            # terminator is missing; do not delete the page body.
            head_end = lower.find("</head>", pos)
            if head_end < 0:
                break
            raw = raw[:last_open] + raw[head_end:]
        else:
            end = first_end + len("</script>")
            # The common corruption also leaves the tail of a previous JSON-LD
            # script after the injected block. Remove that tail through its
            # closing script tag, but only when it is clearly JSON residue.
            second_end = lower.find("</script>", end)
            head_end = lower.find("</head>", end)
            if second_end >= 0 and (head_end < 0 or second_end < head_end):
                residue = raw[end:second_end]
                if re.match(r'\s*(?:[A-Za-z0-9_-]{1,30}"\s*,\s*"item"|[\]}:,])', residue):
                    end = second_end + len("</script>")
            raw = raw[:last_open] + raw[end:]
        changed = True
    return raw, changed

removed_invalid = []
removed_leaks = []
for path in ROOT.rglob("*.html"):
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw, leaked = repair_schema_leaks(raw)
    if leaked:
        removed_leaks.append(path.relative_to(ROOT).as_posix())

    spans = []
    for m in re.finditer(r"<script\\b([^>]*)>(.*?)</script\\s*>", raw, re.I | re.S):
        attrs, body = m.group(1), m.group(2)
        if not re.search(r"""\\btype\\s*=\\s*(["'])application/ld\\+json\\1""", attrs, re.I):
            continue
        try:
            json.loads(body)
        except (json.JSONDecodeError, TypeError):
            spans.append((m.start(), m.end()))
    if spans:
        for start, end in reversed(spans):
            raw = raw[:start] + raw[end:]
        removed_invalid.append((path.relative_to(ROOT).as_posix(), len(spans)))
    if leaked or spans:
        path.write_text(raw, encoding="utf-8")

print(f"Schema leak repair: cleaned {len(removed_leaks)} pages with JSON-LD embedded in markup.")
for name in removed_leaks:
    print(f"- {name}: malformed meta/script fragment removed")
print(f"Invalid JSON-LD repair: removed {sum(n for _, n in removed_invalid)} malformed script blocks across {len(removed_invalid)} pages.")
for name, count in removed_invalid:
    print(f"- {name}: {count} block(s)")
