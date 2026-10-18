#!/usr/bin/env python3
"""Remove leaked JSON-LD markup caused by script tags embedded in <meta> attributes.

This runs late in the production build, after schema injection. It removes only
malformed meta/script fragments; normal page content, layout and valid schema
blocks remain untouched.
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
            last_gt = lower.rfind(">", 0, pos)
            # A <meta> opener after the last closed tag means the script marker
            # has been swallowed into that meta's still-open attribute value.
            if meta_start > last_gt:
                malformed_meta = meta_start
                break
            pos = lower.find(MARKER, pos + len(MARKER))
        if malformed_meta < 0:
            break

        first_end = lower.find("</script>", pos)
        if first_end < 0:
            head_end = lower.find("</head>", pos)
            if head_end < 0:
                break
            end = head_end
        else:
            end = first_end + len("</script>")
            # Some corrupted pages also contain the tail of an earlier JSON-LD
            # graph immediately after the injected block. Remove that residue
            # through its close tag, but only when it looks like JSON residue.
            second_end = lower.find("</script>", end)
            head_end = lower.find("</head>", end)
            if second_end >= 0 and (head_end < 0 or second_end < head_end):
                residue = raw[end:second_end]
                if re.match(r'\s*(?:[A-Za-z0-9_-]{1,30}"\s*,\s*"item"|[\]}:,])', residue):
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
