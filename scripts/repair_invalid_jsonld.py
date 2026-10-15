#!/usr/bin/env python3
"""Remove syntactically invalid JSON-LD script blocks from HTML without touching page content/layout.

Invalid JSON-LD cannot be consumed by search engines. This narrowly removes only a
<script type="application/ld+json"> block whose body fails JSON parsing; valid
JSON-LD blocks, visible content, styles, canonical tags and navigation are unchanged.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".vercel"}

def attr(tag, name):
    m = re.search(r"\\b" + re.escape(name) + r"\\s*=\\s*([\"']) (.*?)\\1".replace(" ", ""), tag, re.I | re.S)
    return m.group(2) if m else ""

removed = []
for path in ROOT.rglob("*.html"):
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    raw = path.read_text(encoding="utf-8", errors="ignore")
    spans = []
    for m in re.finditer(r"<script\\b([^>]*)>(.*?)</script\\s*>", raw, re.I | re.S):
        attrs, body = m.group(1), m.group(2)
        if not re.search(r"""\\btype\\s*=\\s*([\"'])application/ld\\+json\\1""", attrs, re.I):
            continue
        try:
            json.loads(body)
        except (json.JSONDecodeError, TypeError):
            spans.append((m.start(), m.end()))
    if not spans:
        continue
    for start, end in reversed(spans):
        raw = raw[:start] + raw[end:]
    path.write_text(raw, encoding="utf-8")
    removed.append((path.relative_to(ROOT).as_posix(), len(spans)))

print(f"Invalid JSON-LD repair: removed {sum(n for _, n in removed)} malformed script blocks across {len(removed)} pages.")
for name, count in removed:
    print(f"- {name}: {count} block(s)")
