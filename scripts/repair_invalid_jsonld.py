#!/usr/bin/env python3
"""Repair leaked JSON-LD caused by broken HTML openers before injected schema."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".vercel"}
MARKER_RE = re.compile(r'<script\b(?=[^<>]*\bdata-mba-schema\s*=\s*["\']seo-geo-aeo["\'])[^<>]*>', re.I)

def repair_schema_leaks(raw):
    """Remove only malformed opener + injected schema + orphaned JSON-LD tail.

    Corrupt pages include both '<meta content="webs<script ...' and '<s<script ...'.
    In either case the last '<' before the injected script has no '>' before the
    marker, proving an unfinished HTML tag swallowed the script opener.
    """
    changed = False
    while True:
        lower = raw.lower()
        marker = MARKER_RE.search(raw)
        if not marker:
            break
        pos = marker.start()
        opener = lower.rfind("<", 0, pos)
        # A healthy schema script has no unfinished tag immediately before it.
        if opener < 0 or lower.find(">", opener, pos) >= 0:
            # Search for a later malformed occurrence instead of stopping early.
            later = MARKER_RE.search(raw, marker.end())
            found = False
            while later:
                p = later.start()
                o = lower.rfind("<", 0, p)
                if o >= 0 and lower.find(">", o, p) < 0:
                    marker, pos, opener, found = later, p, o, True
                    break
                later = MARKER_RE.search(raw, later.end())
            if not found:
                break

        head_end = lower.find("</head>", pos)
        first_end = lower.find("</script", marker.end())
        if first_end < 0 or (head_end >= 0 and first_end >= head_end):
            # Don't risk deleting the remainder of a document; remove the
            # malformed opener through the end of the head if available.
            if head_end < 0:
                break
            end = head_end
        else:
            close_end = lower.find(">", first_end)
            end = close_end + 1 if close_end >= 0 else first_end + len("</script>")
            # The malformed fragment often contains a dangling tail from a
            # previous JSON-LD graph after the injected script. Consume that
            # tail through the next closing script tag, but only within <head>.
            second_end = lower.find("</script", end)
            if second_end >= 0 and (head_end < 0 or second_end < head_end):
                second_close = lower.find(">", second_end)
                end = second_close + 1 if second_close >= 0 else second_end + len("</script>")
        raw = raw[:opener] + raw[end:]
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

print(f"Schema leak repair: cleaned {len(removed_leaks)} pages with malformed JSON-LD markup.")
for name in removed_leaks:
    print(f"- {name}: malformed opener/schema/orphaned tail removed")
print(f"Invalid JSON-LD repair: removed {sum(n for _, n in removed_invalid)} malformed script blocks across {len(removed_invalid)} pages.")
for name, count in removed_invalid:
    print(f"- {name}: {count} block(s)")
