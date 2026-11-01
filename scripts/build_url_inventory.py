#!/usr/bin/env python3
"""Read-only inventory of sitemap URLs, local HTML files and Vercel routes."""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from html import unescape
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://collegedecoded.in"


class Meta(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals, self.title_parts, self.h1_parts = [], [], []
        self.description, self.capture, self.h1_count = "", None, 0
        self.noindex, self.client_redirect = False, ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = dict(attrs)
        if tag == "link" and "canonical" in (a.get("rel") or "").lower().split() and a.get("href"):
            self.canonicals.append(a["href"].strip())
        elif tag == "meta" and (a.get("name") or "").lower() == "description":
            self.description = (a.get("content") or "").strip()
        elif tag == "meta" and (a.get("name") or "").lower() == "robots":
            self.noindex = "noindex" in (a.get("content") or "").lower()
        elif tag == "title":
            self.capture = "title"
        elif tag == "h1":
            self.h1_count += 1
            self.capture = "h1"

    def handle_endtag(self, tag):
        tag = tag.lower()
        if (tag == "title" and self.capture == "title") or (tag == "h1" and self.capture == "h1"):
            self.capture = None

    def handle_data(self, data):
        if self.capture == "title":
            self.title_parts.append(data)
        elif self.capture == "h1":
            self.h1_parts.append(data)

    def clean(self, parts):
        return re.sub(r"\s+", " ", " ".join(parts)).strip()

    @property
    def title(self):
        return self.clean(self.title_parts)

    @property
    def h1(self):
        return self.clean(self.h1_parts)


def path_of(value):
    path = unquote(urlsplit(value or "").path or "/")
    return path[:-1] if len(path) > 1 and path.endswith("/") else path


def page_file(route):
    route = path_of(route)
    if route == "/":
        p = ROOT / "index.html"
        return p if p.is_file() else None
    slug = route.lstrip("/")
    p = ROOT / (slug + ".html")
    if p.is_file():
        return p
    p = ROOT / "college-cms" / "content" / slug / "overview.html"
    return p if p.is_file() else None


def route_for_file(p):
    rel = p.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.startswith("college-cms/content/") and rel.endswith("/overview.html"):
        return "/" + rel.split("/")[-2]
    return "/" + p.stem


def metadata(p):
    m = Meta()
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        m.canonicals = [x.get("href", "").strip() for x in soup.find_all("link", rel=lambda value: value and "canonical" in value)]
        m.title_parts = [soup.title.get_text(" ", strip=True)] if soup.title else []
        descriptions = soup.find_all("meta", attrs={"name": re.compile(r"^description$", re.I)})
        m.description = (descriptions[0].get("content") or "").strip() if descriptions else ""
        robots = [x.get("content", "") for x in soup.find_all("meta", attrs={"name": re.compile(r"^robots$", re.I)})]
        m.noindex = any("noindex" in value.lower() for value in robots)
        h1s = soup.find_all("h1")
        m.h1_count = len(h1s)
        m.h1_parts = [h1s[0].get_text(" ", strip=True)] if h1s else []
        needle = "location" + ".replace("
        if needle in raw:
            tail = raw.split(needle, 1)[1].lstrip()
            if tail and (tail[0] == chr(34) or tail[0] == chr(39)):
                quote = tail[0]
                end = tail.find(quote, 1)
                if end > 0:
                    m.client_redirect = tail[1:end]
    except OSError:
        pass
    return m
def canonical_is_self(canonical, route):
    if not canonical:
        return False
    parsed = urlsplit(canonical)
    return parsed.netloc.lower() in {"collegedecoded.in", "www.collegedecoded.in"} and path_of(canonical) == route


def rules_for(route, rules, field):
    wanted = path_of(route)
    return [r for r in rules if path_of(r.get(field, "")) == wanted]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/url-inventory")
    args = parser.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = []
    for node in sitemap.findall("s:url", ns):
        loc = node.findtext("s:loc", "", ns).strip()
        if loc:
            entries.append({"url": loc, "path": path_of(loc),
                            "lastmod": node.findtext("s:lastmod", "", ns).strip()})

    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    rules = []
    for kind, key in (("redirect", "redirects"), ("rewrite", "rewrites")):
        for item in config.get(key, []) or []:
            if item.get("source"):
                rules.append({"kind": kind, **item})

    files = sorted(list(ROOT.glob("*.html")) +
                   list((ROOT / "college-cms" / "content").glob("*/overview.html")))
    used, rows, canonical_map = set(), [], defaultdict(list)
    for entry in entries:
        route = entry["path"]
        p = page_file(route)
        m = metadata(p) if p else Meta()
        canonical = m.canonicals[0] if m.canonicals else ""
        canonical_state = ("no_backing_file" if not p else
                           "missing" if not canonical else
                           "self" if canonical_is_self(canonical, route) else "different")
        if canonical and not m.noindex:
            canonical_map[canonical].append(route)
        if p:
            used.add(p.relative_to(ROOT).as_posix())
        outgoing = rules_for(route, rules, "source")
        incoming = rules_for(route, rules, "destination")
        action = "normal"
        if any(x["kind"] == "redirect" for x in outgoing):
            action = "redirect"
        elif any(x["kind"] == "rewrite" for x in outgoing):
            action = "rewrite"
        rows.append({
            "record_type": "sitemap_url", "url_or_source": entry["url"], "path": route,
            "sitemap_lastmod": entry["lastmod"],
            "file": p.relative_to(ROOT).as_posix() if p else "",
            "file_exists": bool(p), "canonical": canonical, "canonical_state": canonical_state,
            "robots_noindex": m.noindex, "client_redirect_target": m.client_redirect,
            "title": m.title, "h1": m.h1, "h1_count": m.h1_count,
            "meta_description_present": bool(m.description), "route_action": action,
            "redirect_or_rewrite_out": " ; ".join(x["kind"] + ":" + x.get("destination", "") for x in outgoing),
            "redirect_or_rewrite_in": " ; ".join(x["kind"] + ":" + x.get("source", "") for x in incoming),
            "destination_file_exists": ""
        })

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if rel in used:
            continue
        route = route_for_file(p)
        m = metadata(p)
        canonical = m.canonicals[0] if m.canonicals else ""
        canonical_state = "missing" if not canonical else ("self" if canonical_is_self(canonical, route) else "different")
        if canonical and not m.noindex:
            canonical_map[canonical].append(route)
        outgoing = rules_for(route, rules, "source")
        incoming = rules_for(route, rules, "destination")
        action = "file_only"
        if any(x["kind"] == "redirect" for x in outgoing):
            action = "redirect_shadows_file"
        elif any(x["kind"] == "rewrite" for x in outgoing):
            action = "rewrite_shadows_file"
        rows.append({
            "record_type": "html_file_not_in_sitemap", "url_or_source": BASE_URL + route,
            "path": route, "sitemap_lastmod": "", "file": rel, "file_exists": True,
            "canonical": canonical, "canonical_state": canonical_state, "robots_noindex": m.noindex,
            "client_redirect_target": m.client_redirect, "title": m.title,
            "h1": m.h1, "h1_count": m.h1_count, "meta_description_present": bool(m.description),
            "route_action": action,
            "redirect_or_rewrite_out": " ; ".join(x["kind"] + ":" + x.get("destination", "") for x in outgoing),
            "redirect_or_rewrite_in": " ; ".join(x["kind"] + ":" + x.get("source", "") for x in incoming),
            "destination_file_exists": ""
        })

    for r in rules:
        source = path_of(r.get("source", ""))
        dest = r.get("destination", "")
        dest_path = path_of(dest)
        dest_file = page_file(dest_path) if dest_path and not dest_path.startswith("/api/") else None
        rows.append({
            "record_type": "vercel_" + r["kind"], "url_or_source": BASE_URL + source,
            "path": source, "sitemap_lastmod": "", "file": "", "file_exists": "",
            "canonical": "", "canonical_state": "", "title": "", "h1": "", "h1_count": "",
            "meta_description_present": "", "route_action": r["kind"] + ("_permanent" if r.get("permanent") else ""),
            "redirect_or_rewrite_out": dest, "redirect_or_rewrite_in": "",
            "destination_file_exists": ("API handler" if dest_path.startswith("/api/") else bool(dest_file))
        })

    fields = ["record_type", "url_or_source", "path", "sitemap_lastmod", "file", "file_exists",
              "canonical", "canonical_state", "robots_noindex", "client_redirect_target", "title", "h1", "h1_count",
              "meta_description_present", "route_action", "redirect_or_rewrite_out",
              "redirect_or_rewrite_in", "destination_file_exists"]
    with (out / "url-inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    (out / "url-inventory.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    srows = [r for r in rows if r["record_type"] == "sitemap_url"]
    frows = [r for r in rows if r["record_type"] == "html_file_not_in_sitemap"]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sitemap_url_count": len(srows),
        "root_html_count": len(list(ROOT.glob("*.html"))),
        "cms_overview_html_count": len(list((ROOT / "college-cms" / "content").glob("*/overview.html"))),
        "explicit_redirect_count": sum(r["kind"] == "redirect" for r in rules),
        "explicit_rewrite_count": sum(r["kind"] == "rewrite" for r in rules),
        "sitemap_urls_without_backing_file": sum(not r["file_exists"] for r in srows),
        "sitemap_urls_missing_canonical": sum(r["canonical_state"] == "missing" for r in srows),
        "sitemap_urls_with_nonself_canonical": sum(r["canonical_state"] == "different" for r in srows),
        "sitemap_urls_missing_title": sum(not r["title"] for r in srows),
        "sitemap_urls_without_exactly_one_h1": sum(r["h1_count"] != 1 for r in srows),
        "sitemap_urls_missing_meta_description": sum(not r["meta_description_present"] for r in srows),
        "html_files_not_in_sitemap": len(frows),
        "files_shadowed_by_redirect_or_rewrite": sum("shadows_file" in r["route_action"] for r in frows),
        "duplicate_canonical_values": sum(len(v) > 1 for v in canonical_map.values()),
        "sitemap_noindex_files": sum(r.get("robots_noindex") is True for r in srows),
        "sitemap_urls_rewritten_to_gone": sum("/api/gone" in r.get("redirect_or_rewrite_out", "") for r in srows)
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = ["# CollegeDecoded URL inventory", "",
              "Generated from the checked-out repository. This is a source inventory, not a live HTTP crawl or a Google Search Console report.", "",
              "## Counts", ""]
    report += [f"- **{k.replace('_', ' ')}:** {v}" for k, v in summary.items()]
    report += ["", "## Interpretation", "",
               "- CSV contains each sitemap URL, each HTML file not represented in the sitemap, and every explicit Vercel redirect/rewrite.",
               "- Canonical tags are read from local HTML. Live response headers, deployed routing and indexability require a separate production crawl.",
               "- Exact static route matches are resolved; dynamic Vercel patterns are recorded but not emulated.",
               "- This tool never changes pages, redirects, noindex directives or sitemap entries.", ""]
    (out / "summary.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
