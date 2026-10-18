#!/usr/bin/env python3
"""Remove leaked JSON-LD markup caused by script tags embedded in <meta> attributes.

The SEO-Geo schema injector has occasionally inserted a script inside an
unfinished meta attribute, causing raw JSON to render before the page hero.
This repair targets that malformed fragment across all HTML pages.
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
        malformed_meta = -1
        while pos >= 0:
            meta_start = lower.rfind("<meta", 0, pos)
            # The meta tag is broken if no closing angle bracket exists between
            # its opener and the injected script marker.
            if meta_start >= 0 and lower.find(">", meta_start, pos) < 0:
                malformed_meta = meta_start
                break
            pos = lower.find(MARKER, pos + len(MARKER))
        if malformed_meta < 0:
            break

        head_end = lower.find("</head>", pos)
        first_end = lower.find("</script>", pos)
        if first_end < 0 or (head_end >= 0 and first_end > head_end):
            if head_end < 0:
                break
            end = head_end
        else:
            end = first_end + len("</script>")
            # A malformed injection often leaves the tail of the previous
            # JSON-LD script after the injected block. In this malformed-meta
            # case, consume that tail through its closing script tag too.
            second_end = lower.find("</script>", end)
            if second_end >= 0 and (head_end < 0 or second_end < head_end):
                end = second_end + len("</script>")
        raw = raw[:malformed_meta] + raw[end:]
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
    for m in re.finditer(r"<script\b([^>]*)>(.*?)</script\s*>", raw, re.I | re.S):
        attrs, body = m.group(1), m.group(2)
        if not re.search(r"""\btype\s*=\s*(["'])application/ld\+json\1""", attrs, re.I):
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
