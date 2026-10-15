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
    print(f"Malformed SEO head repair: {len(repaired)} pages repaired.")
    for name in repaired[:80]:
        print(name)

if __name__ == "__main__":
    main()
