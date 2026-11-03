#!/usr/bin/env python3
"""Fail the build if the ranking hub's server-rendered and interactive data drift."""
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
    raw,
    flags=re.I | re.S,
)
if not block:
    fail("server-rendered college table markers are missing")

rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", block.group(1), flags=re.I | re.S)
if not rows:
    fail("no server-rendered college rows found")

def text_of(markup):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()

ranked = 0
additional = 0
seen_urls = set()
rank_72 = None

for number, row in enumerate(rows, start=1):
    cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.I | re.S)
    if len(cells) != 4:
        fail(f"row {number} has {len(cells)} cells instead of 4")

    rank = text_of(cells[0])
    name = text_of(cells[1])
    city = text_of(cells[2])
    if not name:
        fail(f"row {number} has no institution name")
    if not city or city.casefold() == "management":
        fail(f"row {number} has invalid City, State value: {city!r}")
    if "`" in name:
        fail(f"row {number} contains a stray backtick in its institution name")

    if rank == "Additional":
        additional += 1
    elif re.fullmatch(r"#\d+", rank):
        ranked += 1
        rank_number = int(rank[1:])
        if rank_number == 72:
            rank_72 = (name, re.search(r"<a\b[^>]*href=[\"']([^\"']+)", cells[1], flags=re.I))
    else:
        fail(f"row {number} has an invalid rank label: {rank!r}")

    link = re.search(r"<a\b[^>]*href=[\"']([^\"']+)", cells[1], flags=re.I)
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
        if url in seen_urls:
            fail(f"duplicate profile URL in ranking table: {url}")
        seen_urls.add(url)

if ranked < 80:
    fail(f"expected at least 80 NIRF-ranked institutions, found {ranked}")
if additional < 10:
    fail(f"expected additional profiles to be clearly labelled, found {additional}")
if rank_72 is None or rank_72[0] != "Institute of Management Technology, Hyderabad":
    fail("rank 72 must identify IMT Hyderabad from the source ranking data")
if rank_72[1] is not None:
    fail("rank 72 IMT Hyderabad must not link to the IMT Nagpur profile")

count = re.search(r'<strong\b[^>]*id=["\']count["\'][^>]*>(.*?)</strong>', raw, flags=re.I | re.S)
if not count or not re.search(rf"\b{len(rows)}\s+institutions\s+listed\b", text_of(count.group(1)), flags=re.I):
    fail("initial institution count does not match the server-rendered row count")

if "Array.from(rows.querySelectorAll('tr'))" not in raw:
    fail("client-side filters are not derived from the server-rendered rows")
if "if(!Number.isFinite(n))return false" not in raw:
    fail("rank filters must exclude additional/unranked profiles")
if "match(/#(\\d+)/)" not in raw:
    fail("client-side rank parser must extract numeric NIRF ranks")
if text_of(re.findall(r"<td\b[^>]*>(.*?)</td>", rows[0], flags=re.I | re.S)[0]) != "#1":
    fail("first ranking row must retain NIRF rank #1")
if text_of(re.findall(r"<td\b[^>]*>(.*?)</td>", rows[1], flags=re.I | re.S)[0]) != "#2":
    fail("second ranking row must retain NIRF rank #2")
if "(c.rank?'#'+c.rank:'Additional')" not in raw:
    fail("client-side rendering must reserve Additional for unranked profiles")

print(
    "RANKING HUB VALIDATION PASSED:",
    f"{ranked} ranked rows, {additional} additional profiles,",
    f"{len(rows)} total rows, {len(seen_urls)} unique profile URLs."
)
