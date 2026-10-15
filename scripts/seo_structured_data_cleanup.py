#!/usr/bin/env python3
"""Remove redundant standalone WebPage JSON-LD when a richer graph already describes the same canonical URL.

This script changes only structured-data script blocks. It does not modify visible content,
CSS, layout, navigation, routes, or canonical URLs.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"

def canonical_url(raw):
    m = re.search(r'<link\b(?=[^>]*\brel=["\'][^"\']*canonical[^"\']*["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>', raw, re.I)
    return m.group(1).rstrip("/") if m else ""

def jsonld_blocks(raw):
    out = []
    for m in re.finditer(r'<script\b([^>]*)>(.*?)</script>', raw, re.I | re.S):
        if re.search(r'\btype=["\']application/ld\+json["\']', m.group(1), re.I):
            try:
                payload = json.loads(m.group(2))
            except (json.JSONDecodeError, TypeError):
                continue
            out.append({"start": m.start(), "end": m.end(), "payload": payload, "raw": m.group(0)})
    return out

def nodes(payload):
    if not isinstance(payload, dict):
        return []
    graph = payload.get("@graph")
    return graph if isinstance(graph, list) else [payload]

changed = []
for path in ROOT.rglob("*.html"):
    if any(part in {".git", "node_modules", ".vercel"} for part in path.parts):
        continue
    raw = path.read_text(encoding="utf-8", errors="ignore")
    canonical = canonical_url(raw)
    if not canonical.startswith(BASE):
        continue
    blocks = jsonld_blocks(raw)
    richer_webpage_urls = set()
    for block in blocks:
        payload = block["payload"]
        graph = payload.get("@graph") if isinstance(payload, dict) else None
        if not isinstance(graph, list) or len(graph) < 2:
            continue
        has_webpage = any(isinstance(n, dict) and n.get("@type") == "WebPage" and str(n.get("url", "")).rstrip("/") == canonical for n in graph)
        has_other_entity = any(isinstance(n, dict) and n.get("@type") != "WebPage" for n in graph)
        if has_webpage and has_other_entity:
            richer_webpage_urls.add(canonical)

    remove = []
    for block in blocks:
        payload = block["payload"]
        if isinstance(payload, dict) and payload.get("@type") == "WebPage" and str(payload.get("url", "")).rstrip("/") in richer_webpage_urls and str(payload.get("url", "")).rstrip("/") == canonical:
            remove.append((block["start"], block["end"]))
    if remove:
        for start, end in reversed(remove):
            raw = raw[:start] + raw[end:]
        path.write_text(raw, encoding="utf-8")
        changed.append(path.relative_to(ROOT).as_posix())

print(f"Structured-data cleanup removed redundant standalone WebPage blocks from {len(changed)} pages.")
if changed:
    print("\n".join(changed[:50]))
