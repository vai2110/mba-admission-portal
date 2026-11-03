#!/usr/bin/env python3
"""Apply conservative mobile fixes to static HTML pages during the Vercel build."""
from pathlib import Path
from bs4 import BeautifulSoup
import re

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"404.html", "content-audit.html", "college-page-audit-dashboard.html",
            "github-direct-edit-test.html", "irma-deploy-trigger.html"}
WRAPPER_CLASSES = {"table-wrapper", "table-wrap", "table-responsive",
                   "table-container", "responsive-table", "mobile-table-scroll"}

summary = {"pages_scanned": 0, "viewports_added": 0, "tables_wrapped": 0,
           "mobile_nav_added": 0, "pages_changed": 0}

for path in sorted(ROOT.glob("*.html")):
    if path.name in EXCLUDED:
        continue
    summary["pages_scanned"] += 1
    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    changed = False

    # Ensure mobile viewport metadata exists on every public root HTML page.
    if not soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)}):
        head = soup.find("head")
        if head:
            viewport = soup.new_tag("meta", attrs={"name": "viewport",
                                                    "content": "width=device-width, initial-scale=1"})
            head.insert(0, viewport)
            summary["viewports_added"] += 1
            changed = True

    # Wrap wide tables in a local scrolling container without changing table data.
    for table in soup.find_all("table"):
        parent = table.parent
        already_wrapped = False
        for _ in range(4):
            if not parent or getattr(parent, "name", None) in {"body", "html"}:
                break
            classes = set(parent.get("class") or [])
            style = re.sub(r"\s+", "", parent.get("style", "")).lower()
            if classes & WRAPPER_CLASSES or "overflow-x:auto" in style or "overflow:auto" in style:
                already_wrapped = True
                break
            parent = parent.parent
        if not already_wrapped:
            wrapper = soup.new_tag("div", attrs={"class": ["table-wrapper", "mobile-table-scroll"]})
            table.wrap(wrapper)
            summary["tables_wrapped"] += 1
            changed = True

    # Where a desktop sidebar contains section anchors, expose the same links
    # as a compact mobile-only disclosure menu. It remains hidden on desktop.
    sidebar = soup.select_one(".sidebar")
    if sidebar and not soup.select_one(".mobile-on-page"):
        anchors = []
        seen = set()
        for link in sidebar.find_all("a", href=True):
            href = link.get("href", "").strip()
            label = link.get_text(" ", strip=True)
            if href.startswith("#") and len(href) > 1 and label and href not in seen:
                anchors.append((href, label))
                seen.add(href)
        if anchors:
            nav = soup.new_tag("nav", attrs={"class": ["mobile-on-page"],
                                             "aria-label": "On this page",
                                             "style": "display:none"})
            details = soup.new_tag("details")
            summary_tag = soup.new_tag("summary")
            summary_tag.string = "On this page"
            details.append(summary_tag)
            for href, label in anchors:
                item = soup.new_tag("a", href=href)
                item.string = label
                details.append(item)
            nav.append(details)
            target = soup.select_one(".page-layout") or soup.select_one("main") or soup.body
            if target:
                target.insert_before(nav)
                summary["mobile_nav_added"] += 1
                changed = True

    if changed:
        path.write_text(str(soup), encoding="utf-8")
        summary["pages_changed"] += 1

print("MOBILE LAYOUT FIXES: " + ", ".join(f"{k}={v}" for k, v in summary.items()))
