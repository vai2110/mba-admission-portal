#!/usr/bin/env python3
"""Repair malformed SEO cluster style/head blocks without touching visible page layout."""
from pathlib import Path
import json
import re
import html

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"
STYLE = """<style id="seo-cluster-links-style">
.seo-cluster-links{margin:24px 0;padding:14px 16px;border:1px solid #dbe7f5;border-radius:10px;background:#f8fbff;font-size:13px;line-height:1.6}
.seo-cluster-links strong{display:block;margin-bottom:6px;color:#173f82}
.seo-cluster-links a{color:#2563eb!important;font-weight:600;text-decoration:none}
.seo-cluster-links a:hover{text-decoration:underline}
</style>"""

def attr(raw, name):
    m = re.search(r'\b' + re.escape(name) + r'\s*=\s*(["\'])(.*?)\1', raw, re.I | re.S)
    return html.unescape(m.group(2)) if m else ""


def repair_embedded_geo_schema(raw):
    """Move SEO-Geo JSON-LD out of an unclosed style block."""
    marker = '<script data-mba-schema="seo-geo-aeo"'
    while True:
        lower = raw.lower()
        head_end = lower.rfind("</head>")
        if head_end < 0:
            return raw
        target = None
        for match in re.finditer(re.escape(marker), lower):
            start = match.start()
            if start < head_end and lower.rfind("<style", 0, start) > lower.rfind("</style>", 0, start):
                target = start
                break
        if target is None:
            return raw
        close_start = lower.find("</script>", target, head_end)
        if close_start < 0:
            return raw
        close_end = close_start + len("</script>")
        block = raw[target:close_end]
        prefix = raw[:target]
        style_start = lower.rfind("<style", 0, target)
        if raw.find(">", style_start, target) < 0:
            prefix = raw[:style_start]
        else:
            partial = re.search(r"</s(?:t(?:y(?:l(?:e)?)?)?)?$", prefix, re.I)
            prefix = prefix[:partial.start()] + "</style>" if partial else prefix + "</style>"
        suffix = raw[close_end:]
        tail_end = suffix.lower().rfind("</head>")
        if tail_end >= 0:
            tail = suffix[:tail_end]
            if re.search(r"</script\s*>", tail, re.I) and not re.search(r"<script\b", tail, re.I):
                keep = [tag for tag in re.findall(r"<(?:meta|link|script)\b[^>]*>", tail, re.I)
                        if tag.lower().startswith("<meta")
                        or (tag.lower().startswith("<link") and re.search(r'\brel\s*=\s*["\']stylesheet["\']', tag, re.I))
                        or (tag.lower().startswith("<script") and re.search(r'\bsrc\s*=', tag, re.I))]
                suffix = "\n".join(keep) + "\n" + suffix[tail_end:]
        raw = prefix + suffix
        head_end = raw.lower().rfind("</head>")
        if head_end >= 0 and block and marker not in raw[:head_end].lower():
            raw = raw[:head_end] + "\n" + block + "\n" + raw[head_end:]

def main():
    repaired = []
    for path in ROOT.rglob("*.html"):
        if any(part in {".git", "node_modules", ".vercel"} for part in path.parts):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        marker = '<style id="seo-cluster-links-style">'
        start = raw.find(marker)
        if start < 0:
            continue
        head_end = raw.lower().find("</head>", start)
        if head_end < 0:
            continue
        # Healthy block: style closes before any JSON-LD script.
        style_end = raw.lower().find("</style>", start, head_end)
        schema_at = raw.lower().find('<script data-mba-schema="seo-geo-aeo"', start, head_end)
        if style_end >= 0 and (schema_at < 0 or style_end < schema_at):
            continue

        head = raw[:start]
        tail = raw[start:head_end]
        title_match = re.search(r"<title\b[^>]*>(.*?)</title>", raw, re.I | re.S)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else path.stem.replace("-", " ").title()
        desc_match = re.search(r'<meta\b(?=[^>]*\bname\s*=\s*["\']description["\'])([^>]*)>', raw, re.I | re.S)
        desc = attr(desc_match.group(0), "content") if desc_match else ""
        canonical_match = re.search(r'<link\b(?=[^>]*\brel\s*=\s*["\']canonical["\'])([^>]*)>', raw, re.I | re.S)
        canonical = attr(canonical_match.group(0), "href") if canonical_match else BASE + ("" if path.name == "index.html" else "/" + path.stem)

        # Preserve legitimate external/local stylesheet links and script includes from the rest of the head.
        preserved = []
        for tag in re.findall(r"<(?:link|script)\b[^>]*>", tail, re.I | re.S):
            if tag.lower().startswith("<link") and re.search(r'\brel\s*=\s*["\']stylesheet["\']', tag, re.I):
                if "seo-cluster-links-style" not in tag:
                    preserved.append(tag)
            elif tag.lower().startswith("<script") and re.search(r'\bsrc\s*=', tag, re.I):
                preserved.append(tag)

        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type":"WebPage","@id":canonical+"#webpage","url":canonical,"name":title,"description":desc,"inLanguage":"en-IN","isPartOf":{"@id":BASE+"/#website"}},
                {"@type":"BreadcrumbList","@id":canonical+"#breadcrumb","itemListElement":[
                    {"@type":"ListItem","position":1,"name":"Home","item":BASE+"/"},
                    {"@type":"ListItem","position":2,"name":title,"item":canonical}
                ]}
            ]
        }
        replacement = STYLE + "\n<script data-mba-schema=\"seo-geo-aeo\" type=\"application/ld+json\">" + json.dumps(schema, ensure_ascii=False) + "</script>\n" + "\n".join(dict.fromkeys(preserved)) + "\n"
        raw = head + replacement + raw[head_end:]
        path.write_text(raw, encoding="utf-8")
        repaired.append(path.relative_to(ROOT).as_posix())

    # Repair page-specific styles too, not only the shared cluster-link style.
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in {".git", "node_modules", ".vercel"} for part in path.parts):
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        updated = repair_embedded_geo_schema(raw)
        if updated != raw:
            path.write_text(updated, encoding="utf-8")
            name = path.relative_to(ROOT).as_posix()
            if name not in repaired:
                repaired.append(name)
    print(f"Malformed SEO head repair: {len(repaired)} pages repaired.")
    for name in repaired[:80]:
        print(name)

if __name__ == "__main__":
    main()
