#!/usr/bin/env python3
"""Idempotently link the fixed CollegeDecoded 50-URL priority set to its parent and siblings.

Runs late in the build, after content/page generators, so links are present in final HTML.
It only edits the listed college-family pages plus the IIM Nagpur parent/placements pages.
It does not change page copy, canonical tags, robots directives, redirects, or sitemap membership.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://collegedecoded.in"

GROUPS = {
    "alliance-university": [
        "alliance-university-bba", "alliance-university-bba-llb",
        "alliance-university-bca", "alliance-university-bcom",
        "alliance-university-btech-ai-data-science", "alliance-university-btech-cse",
        "alliance-university-mba", "alliance-university-placements",
    ],
    "anna-university": [
        "anna-university-admission-2026", "anna-university-fees-placements",
        "anna-university-btech-cse", "anna-university-mba",
    ],
    "iim-mumbai": [
        "iim-mumbai-placements", "iim-mumbai-mba",
        "iim-mumbai-mba-oscm", "iim-mumbai-mba-sm",
    ],
    "iim-nagpur": [
        "indian-institute-of-management-nagpur-mba",
        "indian-institute-of-management-nagpur-blended-mba-for-working-professionals",
        "indian-institute-of-management-nagpur-executive-mba-hybrid",
        "iim-nagpur-placements",
    ],
    "iim-rohtak": [
        "iim-rohtak-ipm", "iim-rohtak-pgp", "iim-rohtak-pgpx",
        "iim-rohtak-placements",
    ],
    "iit-roorkee": [
        "iit-roorkee-placements", "iit-roorkee-executive-mba", "iit-roorkee-mba",
    ],
    "imt-ghaziabad": ["imt-ghaziabad-placements"],
    "jims-rohini": [
        "jims-rohini-admission-2026", "jims-rohini-fees", "jims-rohini-pgdm",
        "jims-rohini-pgdm-ib", "jims-rohini-fees-placements", "jims-rohini-placements",
    ],
    "nmims": [
        "nmims-placements", "nmims-mba", "nmims-mba-pharma-tech", "nmims-mba-tech",
    ],
    "sibm-bengaluru": [
        "sibm-bengaluru-placements", "sibm-bengaluru-mba",
        "sibm-bengaluru-mba-business-analytics", "sibm-bengaluru-mba-executive",
    ],
}

LABELS = {
    "alliance-university": "Alliance University overview",
    "anna-university": "Anna University overview",
    "iim-mumbai": "IIM Mumbai overview",
    "iim-nagpur": "IIM Nagpur overview",
    "iim-rohtak": "IIM Rohtak overview",
    "iit-roorkee": "IIT Roorkee overview",
    "imt-ghaziabad": "IMT Ghaziabad overview",
    "jims-rohini": "JIMS Rohini overview",
    "nmims": "NMIMS overview",
    "sibm-bengaluru": "SIBM Bengaluru overview",
}
SPECIAL = {
    "alliance-university-bba": "BBA",
    "alliance-university-bba-llb": "BBA LL.B.",
    "alliance-university-bca": "BCA",
    "alliance-university-bcom": "BCom",
    "alliance-university-btech-ai-data-science": "BTech AI & Data Science",
    "alliance-university-btech-cse": "BTech CSE",
    "alliance-university-mba": "MBA",
    "anna-university-admission-2026": "Admission 2026",
    "anna-university-fees-placements": "Fees & placements",
    "anna-university-btech-cse": "BTech CSE",
    "anna-university-mba": "MBA",
    "iim-mumbai-placements": "Placements",
    "iim-mumbai-mba": "MBA",
    "iim-mumbai-mba-oscm": "MBA OSCM",
    "iim-mumbai-mba-sm": "MBA SM",
    "indian-institute-of-management-nagpur-mba": "MBA",
    "indian-institute-of-management-nagpur-blended-mba-for-working-professionals": "Blended MBA for working professionals",
    "indian-institute-of-management-nagpur-executive-mba-hybrid": "Executive MBA (Hybrid)",
    "iim-nagpur-placements": "Placements",
    "iim-rohtak-ipm": "Integrated Programme in Management (IPM)",
    "iim-rohtak-pgp": "Post Graduate Programme (PGP)",
    "iim-rohtak-pgpx": "PGPX",
    "iim-rohtak-placements": "Placements",
    "iit-roorkee-placements": "Placements",
    "iit-roorkee-executive-mba": "Executive MBA",
    "iit-roorkee-mba": "MBA",
    "imt-ghaziabad-placements": "Placements",
    "jims-rohini-admission-2026": "Admission 2026",
    "jims-rohini-fees": "Fees",
    "jims-rohini-pgdm": "PGDM",
    "jims-rohini-pgdm-ib": "PGDM International Business",
    "jims-rohini-fees-placements": "Fees & placements",
    "jims-rohini-placements": "Placements",
    "nmims-placements": "Placements",
    "nmims-mba": "MBA",
    "nmims-mba-pharma-tech": "MBA Pharmaceutical Management",
    "nmims-mba-tech": "MBA Technology Management",
    "sibm-bengaluru-placements": "Placements",
    "sibm-bengaluru-mba": "MBA",
    "sibm-bengaluru-mba-business-analytics": "MBA Business Analytics",
    "sibm-bengaluru-mba-executive": "Executive MBA",
}

STYLE = """<style id="cd-50-url-parent-links-style">
.cd-50-url-parent-links{margin:22px auto 18px;padding:14px 16px;max-width:1180px;border:1px solid #dbe7f5;border-radius:9px;background:#f8fbff;font-size:13px;line-height:1.8}
.cd-50-url-parent-links strong{display:block;margin:0 0 6px;color:#173f82;font-size:13px}
.cd-50-url-parent-links a{color:#1d4ed8;text-decoration:underline;text-underline-offset:2px;font-weight:600}
.cd-50-url-parent-links .cd-parent-label{font-weight:800}
</style>"""

def label(slug):
    return LABELS.get(slug, SPECIAL.get(slug, slug.replace("-", " ").title()))

def hrefs(html):
    return set(re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', html, flags=re.I))

def clean_target(href):
    href = href.split("#", 1)[0].split("?", 1)[0]
    href = re.sub(r"^https?://(?:www\.)?collegedecoded\.in/", "", href, flags=re.I)
    return href.strip("/").removesuffix(".html")

def insert_before_body(html, block):
    matches = list(re.finditer(r"</body\s*>", html, flags=re.I))
    if not matches:
        return None
    pos = matches[-1].start()
    return html[:pos] + block + "\n" + html[pos:]

def main():
    changed_pages, links_added, missing_files = [], 0, []
    family_report = {}
    for parent, children in GROUPS.items():
        family = [parent] + children
        existing = [slug for slug in family if (ROOT / f"{slug}.html").is_file()]
        missing_files.extend(f"{slug}.html" for slug in family if slug not in existing)
        family_report[parent] = {"existing": existing, "missing": [s for s in family if s not in existing]}
        for source in existing:
            path = ROOT / f"{source}.html"
            original = path.read_text(encoding="utf-8", errors="replace")
            html = re.sub(
                r'<nav\b[^>]*id=["\']cd-50-url-parent-links["\'][^>]*>.*?</nav>\s*',
                "", original, flags=re.I | re.S
            )
            current = {clean_target(h) for h in hrefs(html)}
            desired = [slug for slug in existing if slug != source]
            missing = [slug for slug in desired if slug not in current]
            if not missing:
                if html != original:
                    path.write_text(html, encoding="utf-8")
                    changed_pages.append(source)
                continue
            links = []
            if source != parent:
                links.append(f'<a class="cd-parent-label" href="/{parent}">{label(parent)}</a>')
            for slug in missing:
                links.append(f'<a href="/{slug}">{label(slug)}</a>')
            block = (
                '<nav id="cd-50-url-parent-links" class="cd-50-url-parent-links" '
                'aria-label="Related pages in this college">'
                '<strong>Explore this college and its programmes</strong>'
                + " · ".join(links) + "</nav>"
            )
            updated = insert_before_body(html, block)
            if updated is None:
                missing_files.append(f"{source}.html (no closing body tag)")
                continue
            if "cd-50-url-parent-links-style" not in updated:
                head = re.search(r"</head\s*>", updated, flags=re.I)
                if head:
                    updated = updated[:head.start()] + STYLE + "\n" + updated[head.start():]
            path.write_text(updated, encoding="utf-8")
            changed_pages.append(source)
            links_added += len(links)

    report = {
        "watchlist_groups": len(GROUPS),
        "pages_changed": sorted(set(changed_pages)),
        "links_added": links_added,
        "missing_files_or_structure": sorted(set(missing_files)),
        "families": family_report,
    }
    (ROOT / "seo-audit").mkdir(exist_ok=True)
    (ROOT / "seo-audit" / "50-url-parent-child-link-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "families"}, ensure_ascii=False, indent=2))
    if missing_files:
        raise SystemExit("50-URL parent/child link gate failed: missing source files or body structure.")

if __name__ == "__main__":
    main()
