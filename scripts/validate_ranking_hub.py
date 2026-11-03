#!/usr/bin/env python3
"""Validate the ranking hub's ranked table and separate additional-profiles section."""
from pathlib import Path
import html
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "top-mba-colleges-in-india.html"
BASE = "https://collegedecoded.in"

def fail(message):
    print("RANKING HUB VALIDATION FAILED:", message, file=sys.stderr)
    raise SystemExit(1)

if not PAGE.is_file():
    fail("top-mba-colleges-in-india.html is missing")

raw = PAGE.read_text(encoding="utf-8", errors="replace")
block = re.search(
    r"<!-- SERVER_RENDERED_COLLEGE_LINKS -->(.*?)<!-- /SERVER_RENDERED_COLLEGE_LINKS -->",
    raw, flags=re.I | re.S,
)
if not block:
    fail("server-rendered ranked college table markers are missing")

def text_of(markup):
    return re.sub(r"\\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()

def validate_rows(markup, expected_ranked):
    rows = re.findall(r"<tr\\b[^>]*>(.*?)</tr>", markup, flags=re.I | re.S)
    seen = set()
    ranked = 0
    rank_72 = None
    for number, row in enumerate(rows, start=1):
        cells = re.findall(r"<td\\b[^>]*>(.*?)</td>", row, flags=re.I | re.S)
        if len(cells) != 4:
            fail(f"row {number} has {len(cells)} cells instead of 4")
        rank, name, city = map(text_of, cells[:3])
        if not name:
            fail(f"row {number} has no institution name")
        if not city or city.casefold() == "management":
            fail(f"row {number} has invalid City, State value: {city!r}")
        if "`" in name:
            fail(f"row {number} contains a stray backtick in its institution name")
        if expected_ranked:
            if not re.fullmatch(r"#\\d+", rank):
                fail(f"ranked table row {number} has a non-numeric rank label: {rank!r}")
            ranked += 1
            if int(rank[1:]) == 72:
                rank_72 = (name, re.search(r"<a\\b[^>]*href=[\"']([^\"']+)", cells[1], flags=re.I))
        elif rank.casefold() not in {"additional", "profile"}:
            fail(f"additional profile row {number} has unexpected listing label: {rank!r}")
        link = re.search(r"<a\\b[^>]*href=[\"']([^\"']+)", cells[1], flags=re.I)
        if link:
            url = html.unescape(link.group(1)).strip()
            if url.startswith(BASE):
                path = url[len(BASE):]
            elif url.startswith("/"):
                path = url
            else:
                fail(f"row {number} uses a non-first-party college URL: {url}")
            if ".html" in path.lower() or "?" in path or "#" in path:
                fail(f"row {number} links to a non-canonical URL: {url}")
            if url in seen:
                fail(f"duplicate profile URL in table: {url}")
            seen.add(url)
    return rows, ranked, rank_72

ranked_rows, ranked, rank_72 = validate_rows(block.group(1), True)
if ranked < 80:
    fail(f"expected at least 80 NIRF-ranked institutions, found {ranked}")
if rank_72 is None or rank_72[0] != "Institute of Management Technology, Hyderabad":
    fail("rank 72 must identify IMT Hyderabad from the source ranking data")
if rank_72[1] is not None:
    fail("rank 72 IMT Hyderabad must not link to the IMT Nagpur profile")

additional_section = re.search(
    r'<section\\b[^>]*id=["\']additional-colleges["\'][^>]*>(.*?)</section>',
    raw, flags=re.I | re.S,
)
if not additional_section or not re.search(r"additional", text_of(additional_section.group(1)), flags=re.I):
    fail("a separately labelled additional-colleges section is required")
additional_tables = re.findall(r"<table\\b[^>]*>.*?<tbody[^>]*>(.*?)</tbody>.*?</table>", additional_section.group(1), flags=re.I | re.S)
if not additional_tables:
    fail("additional-colleges section must contain a separate table")
additional_rows, _, _ = validate_rows(additional_tables[0], False)
if len(additional_rows) < 1:
    fail("at least one additional profile is required")

count = re.search(r'<strong\\b[^>]*id=["\']count["\'][^>]*>(.*?)</strong>', raw, flags=re.I | re.S)
if not count or not re.search(r"\\b100\\s+ranked\\s+institutions\\b", text_of(count.group(1)), flags=re.I):
    fail("ranked institution count must clearly state 100 ranked institutions")

if "Array.from(rows.querySelectorAll('tr'))" not in raw:
    fail("client-side filters must be derived from the server-rendered ranked rows")
if "Number(row.dataset.rank)" not in raw:
    fail("rank filters must use numeric rank values from ranked rows")

print(
    "RANKING HUB VALIDATION PASSED:",
    f"{ranked} ranked rows, {len(additional_rows)} additional profiles,",
    f"{len(ranked_rows)} ranked table rows."
)
