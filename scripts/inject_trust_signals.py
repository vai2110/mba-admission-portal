#!/usr/bin/env python3
"""Add source-backed editorial trust signals and consistent breadcrumb schema."""
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
import json
import re
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"
CONFIG = ROOT / "pipeline" / "config.json"
SITEMAP = ROOT / "sitemap.xml"
COLLEGE_INDEX = ROOT / "data" / "management-live-colleges.json"
EXCLUDED_PARTS = {".git", "node_modules", ".github", ".vercel"}
OFFICIAL_HOSTS = {
    "nirfindia.org", "ugc.gov.in", "aicte-india.org", "nta.ac.in",
    "iimcat.ac.in", "jeeadv.ac.in", "josaa.nic.in", "csab.nic.in",
    "naac.gov.in", "nmc.org.in", "education.gov.in", "exams.nta.ac.in",
    "cuet.nta.nic.in", "mcc.nic.in", "nbe.edu.in",
}

config = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
reviewer = (config.get("reviewer") or "").strip()
author = (config.get("author") or "").strip()
college_data = json.loads(COLLEGE_INDEX.read_text(encoding="utf-8")) if COLLEGE_INDEX.exists() else {"colleges": []}
college_by_slug = {}
for name, url in college_data.get("colleges", []):
    slug = urlparse(url).path.strip("/")
    if slug:
        college_by_slug[slug] = name

lastmod_by_path = {}
if SITEMAP.exists():
    try:
        from xml.etree import ElementTree as ET
        tree = ET.parse(SITEMAP)
        for node in tree.findall(".//{*}url"):
            loc = node.find("{*}loc")
            lastmod = node.find("{*}lastmod")
            if loc is not None and loc.text and lastmod is not None and lastmod.text:
                lastmod_by_path[urlparse(loc.text.strip()).path.rstrip("/") or "/"] = lastmod.text.strip()
    except Exception:
        pass

def page_canonical(soup, path):
    tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    if tag and tag.get("href"):
        return tag["href"].strip()
    stem = path.relative_to(ROOT).with_suffix("").as_posix()
    return BASE + ("/" if stem == "index" else "/" + stem)

def date_for(path, canonical):
    value = lastmod_by_path.get(urlparse(canonical).path.rstrip("/") or "/")
    if not value:
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cs", "--", path.relative_to(ROOT).as_posix()],
                cwd=ROOT, capture_output=True, text=True, check=False
            )
            value = result.stdout.strip()
        except Exception:
            value = ""
    if not value:
        return ""
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return value

def is_official(host):
    host = (host or "").lower().split(":")[0]
    if host in OFFICIAL_HOSTS:
        return True
    return host.endswith((".ac.in", ".edu.in", ".gov.in", ".edu"))

def page_title(soup, path):
    node = soup.find("title")
    title = node.get_text(" ", strip=True) if node else path.stem.replace("-", " ").title()
    return re.sub(r"\s*\|\s*CollegeDecoded\s*$", "", title, flags=re.I).strip()

def college_for(stem):
    matches = [slug for slug in college_by_slug if stem == slug or stem.startswith(slug + "-")]
    if not matches:
        return None, None
    slug = max(matches, key=len)
    return slug, college_by_slug[slug]

def breadcrumb_items(stem, title, canonical):
    college_slug, college_name = college_for(stem)
    items = [
        {"name": "Home", "item": BASE + "/"},
        {"name": "Colleges", "item": BASE + "/college-guides"},
    ]
    if college_slug:
        items.append({"name": college_name, "item": BASE + "/" + college_slug})
        if stem != college_slug:
            items.append({"name": title, "item": canonical})
    else:
        items.append({"name": title, "item": canonical})
    return items

def official_sources(soup):
    scope = soup.find("main") or soup.body or soup
    found, seen = [], set()
    for link in scope.find_all("a", href=True):
        href = link["href"].strip()
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"} or not is_official(parsed.hostname):
            continue
        clean_url = href.split("#", 1)[0]
        if clean_url in seen:
            continue
        seen.add(clean_url)
        label = link.get_text(" ", strip=True) or parsed.hostname
        found.append((label, clean_url))
    return found[:20]

def update_breadcrumb_schema(soup, items, canonical, title):
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": canonical + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": item["name"], "item": item["item"]}
            for i, item in enumerate(items)
        ],
    }
    replaced = False
    for script_tag in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        try:
            payload = json.loads(script_tag.string or script_tag.get_text())
        except Exception:
            continue
        graph = payload.get("@graph") if isinstance(payload, dict) else None
        if isinstance(graph, list):
            for node in graph:
                if isinstance(node, dict) and node.get("@type") == "BreadcrumbList":
                    node.clear()
                    node.update({k: v for k, v in breadcrumb.items() if k != "@context"})
                    replaced = True
            if replaced:
                script_tag.string = json.dumps(payload, ensure_ascii=False)
        elif isinstance(payload, dict) and payload.get("@type") == "BreadcrumbList":
            script_tag.string = json.dumps(breadcrumb, ensure_ascii=False)
            replaced = True
    if not replaced:
        node = soup.new_tag("script", attrs={"type": "application/ld+json"})
        node.string = json.dumps(breadcrumb, ensure_ascii=False)
        (soup.head or soup).append(node)

def add_homepage_identity_schema(soup):
    existing_types = set()
    for script_tag in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        try:
            payload = json.loads(script_tag.string or script_tag.get_text())
        except Exception:
            continue
        graph = payload.get("@graph") if isinstance(payload, dict) else None
        nodes = graph if isinstance(graph, list) else [payload]
        for node in nodes:
            if isinstance(node, dict):
                types = node.get("@type", [])
                existing_types.update(types if isinstance(types, list) else [types])
    nodes = []
    if "Organization" not in existing_types:
        nodes.append({
            "@type": "Organization",
            "@id": BASE + "#organization",
            "name": "CollegeDecoded",
            "url": BASE + "/",
            "logo": BASE + "/assets/Collegedecoded%20Logo.jpeg",
        })
    if "WebSite" not in existing_types:
        nodes.append({
            "@type": "WebSite",
            "@id": BASE + "#website",
            "url": BASE + "/",
            "name": "CollegeDecoded",
            "publisher": {"@id": BASE + "#organization"},
            "inLanguage": "en-IN",
        })
    if nodes:
        graph = soup.new_tag("script", attrs={"type": "application/ld+json"})
        graph.string = json.dumps({"@context": "https://schema.org", "@graph": nodes}, ensure_ascii=False)
        (soup.head or soup).append(graph)

def add_visible_breadcrumb(soup, items):
    if soup.select_one(".cd-breadcrumbs"):
        return
    nav = soup.new_tag("nav", attrs={"class": "cd-breadcrumbs", "aria-label": "Breadcrumb"})
    ol = soup.new_tag("ol")
    for i, item in enumerate(items):
        li = soup.new_tag("li")
        if i < len(items) - 1:
            a = soup.new_tag("a", href=item["item"])
            a.string = item["name"]
            li.append(a)
        else:
            span = soup.new_tag("span", attrs={"aria-current": "page"})
            span.string = item["name"]
            li.append(span)
        ol.append(li)
    nav.append(ol)
    header = soup.find("header")
    if header:
        header.insert_after(nav)
    elif soup.body:
        soup.body.insert(0, nav)

def add_editorial_panel(soup, updated_date):
    if soup.select_one(".cd-editorial-author"):
        return
    author_label = author or "[Add author name]"
    reviewer_label = reviewer or "[Add reviewer name]"
    panel = soup.new_tag("div", attrs={"class": "cd-editorial-author", "id": "cdEditorialAuthorStatic"})
    avatar = soup.new_tag("div", attrs={"class": "cd-editorial-avatar", "aria-hidden": "true"})
    avatar.string = "CD"
    copy = soup.new_tag("div", attrs={"class": "cd-editorial-copy"})
    name = soup.new_tag("div", attrs={"class": "cd-editorial-name"})
    name.string = "Author: " + author_label
    sub = soup.new_tag("div", attrs={"class": "cd-editorial-sub"})
    sub.string = "Reviewed by: " + reviewer_label + " | Last updated: " + (updated_date or "[Verify update date]") + " | Data as of: " + (config.get("academic_year") or "2026-2027")
    copy.append(name)
    copy.append(sub)
    panel.append(avatar)
    panel.append(copy)
    target = soup.select_one(".page-layout") or soup.find("main") or soup.body
    if target:
        target.insert_before(panel)

def add_sources_section(soup):
    main = soup.find("main") or soup.body
    if not main:
        return
    if any("source" in h.get_text(" ", strip=True).lower() for h in main.find_all(["h2", "h3"])):
        return
    sources = official_sources(soup)
    if not sources:
        return
    section = soup.new_tag("section", attrs={"class": "cd-official-sources"})
    heading = soup.new_tag("h2")
    heading.string = "Official Sources"
    section.append(heading)
    intro = soup.new_tag("p")
    intro.string = "Use the institute or regulator notice as the final reference before applying or paying fees."
    section.append(intro)
    listing = soup.new_tag("ul")
    for label, href in sources:
        li = soup.new_tag("li")
        a = soup.new_tag("a", href=href, rel="noopener", target="_blank")
        a.string = label[:120]
        li.append(a)
        listing.append(li)
    section.append(listing)
    main.append(section)

STYLE = """
.cd-breadcrumbs{width:min(1180px,calc(100% - 36px));margin:10px auto 14px;color:#64748b;font:12px/1.5 Arial,Helvetica,sans-serif}
.cd-breadcrumbs ol{display:flex;flex-wrap:wrap;gap:6px;list-style:none;margin:0;padding:0}
.cd-breadcrumbs li+li:before{content:"/";margin-right:6px;color:#94a3b8}
.cd-breadcrumbs a{color:#2458d8;text-decoration:none}
.cd-breadcrumbs [aria-current=page]{color:#475569}
.cd-editorial-author{width:min(1180px,calc(100% - 36px));box-sizing:border-box;margin:12px auto 18px;padding:12px 16px;background:#fff;border:1px solid #edf0f5;border-radius:14px;display:flex;align-items:center;gap:11px;color:#475569;font:13px/1.45 Arial,Helvetica,sans-serif}
.cd-editorial-avatar{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:#ff6b1a;color:#fff;font-size:11px;font-weight:800;flex:0 0 34px}
.cd-editorial-copy{min-width:0}.cd-editorial-name{font-weight:800;color:#123b78}.cd-editorial-sub{margin-top:3px;color:#64748b;font-size:11px;overflow-wrap:anywhere}
.cd-official-sources{margin:24px 0;padding:16px 18px;border:1px solid #e6edf6;border-radius:12px;background:#f8fbff}
.cd-official-sources h2{margin-top:0}.cd-official-sources li{margin:5px 0;overflow-wrap:anywhere}.cd-official-sources a{color:#2458d8}
@media(max-width:640px){.cd-breadcrumbs{width:calc(100% - 24px);font-size:11px;margin:8px auto 10px}.cd-editorial-author{width:calc(100% - 24px);margin:10px auto 14px;padding:10px 12px;align-items:flex-start}.cd-editorial-sub{font-size:10px}.cd-official-sources{padding:13px}}
"""

stats = {"pages_scanned": 0, "breadcrumbs_added": 0, "breadcrumb_schema_added_or_updated": 0,
         "editorial_panels_added": 0, "source_sections_added": 0, "identity_schema_added": 0,
         "pages_changed": 0}

for path in sorted(ROOT.rglob("*.html")):
    if any(part in EXCLUDED_PARTS for part in path.parts) or path.name == "404.html":
        continue
    if path.name == "index.html" and path.parent == ROOT:
        raw = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        before = str(soup)
        add_homepage_identity_schema(soup)
        if soup.head and not soup.head.find("style", id="cdEditorialTrustStyles"):
            style = soup.new_tag("style", id="cdEditorialTrustStyles")
            style.string = STYLE
            soup.head.append(style)
        if str(soup) != before:
            path.write_text(str(soup), encoding="utf-8")
            stats["pages_changed"] += 1
            stats["identity_schema_added"] += 1
        continue
    stats["pages_scanned"] += 1
    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    robots = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots and "noindex" in (robots.get("content") or "").lower():
        continue
    before = str(soup)
    canonical = page_canonical(soup, path)
    title = page_title(soup, path)
    stem = path.relative_to(ROOT).with_suffix("").as_posix()
    items = breadcrumb_items(stem, title, canonical)
    had_breadcrumb = soup.select_one(".cd-breadcrumbs") is not None
    add_visible_breadcrumb(soup, items)
    if not had_breadcrumb:
        stats["breadcrumbs_added"] += 1
    update_breadcrumb_schema(soup, items, canonical, title)
    stats["breadcrumb_schema_added_or_updated"] += 1
    if not soup.head or not soup.head.find("style", id="cdEditorialTrustStyles"):
        if soup.head:
            style = soup.new_tag("style", id="cdEditorialTrustStyles")
            style.string = STYLE
            soup.head.append(style)
    if not soup.select_one(".cd-editorial-author"):
        add_editorial_panel(soup, date_for(path, canonical))
        stats["editorial_panels_added"] += 1
    before_sources = soup.select_one(".cd-official-sources") is not None
    add_sources_section(soup)
    if not before_sources and soup.select_one(".cd-official-sources"):
        stats["source_sections_added"] += 1
    if str(soup) != before:
        path.write_text(str(soup), encoding="utf-8")
        stats["pages_changed"] += 1

print("EDITORIAL TRUST INJECTION: " + ", ".join(f"{key}={value}" for key, value in stats.items()))
