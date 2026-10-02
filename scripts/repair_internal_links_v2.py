import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED = {
    "iim-ahmedabad.html", "sibm-pune.html", "404.html", "content-audit.html",
    "college-page-audit-dashboard.html", "github-direct-edit-test.html",
    "irma-deploy-trigger.html", "welingkar-mumbai-links.html",
    "welingkar-mumbai-programmes-note.html", "welingkar-mumbai-programmes.html",
    "mica.html", "mica-pgdm-c.html", "mica-pgdm.html", "mica-placements.html"
}

ALIAS_CLUSTERS = {
    "iim-nagpur.html": [
        "iim-nagpur.html",
        "indian-institute-of-management-nagpur-mba.html",
        "indian-institute-of-management-nagpur-blended-mba-for-working-professionals.html",
        "indian-institute-of-management-nagpur-executive-mba-hybrid.html",
        "iim-nagpur-placements.html",
    ],
    "iit-kanpur.html": [
        "iit-kanpur.html",
        "indian-institute-of-technology-kanpur-mba-programme.html",
        "iit-kanpur-management-sciences-m-tech.html",
        "iit-kanpur-management-sciences-phd.html",
        "iit-kanpur-placements.html",
    ],
    "jaipuria-institute-of-management-lucknow.html": [
        "jaipuria-institute-of-management-lucknow.html",
        "jaipuria-lucknow-fpm.html",
        "jaipuria-lucknow-pgdm.html",
        "jaipuria-lucknow-pgdm-financial-services.html",
        "jaipuria-lucknow-pgdm-retail-management.html",
        "jaipuria-institute-of-management-lucknow-placements.html",
    ],
}

STYLE = """<style id="college-cluster-links-style">
.college-cluster-links{margin:24px 0;padding:14px 16px;border:1px solid #dbe7f5;border-radius:10px;background:#f8fbff;font-size:13px;line-height:1.6}
.college-cluster-links strong{display:block;margin-bottom:6px;color:#173f82}
.college-cluster-links a{color:#2563eb!important;font-weight:600;text-decoration:none}
.college-cluster-links a:hover{text-decoration:underline}
</style>"""

def build_clusters(pages):
    names = set(pages)
    clusters = {}

    for placement in sorted(n for n in pages if n.endswith("-placements.html")):
        base = placement[:-len("-placements.html")] + ".html"
        if base not in names:
            continue
        prefix = base[:-5]
        programmes = sorted(
            n for n in pages
            if n not in {base, placement}
            and n not in EXCLUDED
            and n.startswith(prefix + "-")
        )
        clusters[base] = [base, *programmes, placement]

    for overview, members in ALIAS_CLUSTERS.items():
        if overview not in names:
            continue
        valid = [m for m in members if m in names and m not in EXCLUDED]
        if len(valid) >= 2:
            clusters[overview] = valid

    return clusters

def label(name, members):
    if name == members[0]:
        return "Overview"
    if name.endswith("-placements.html"):
        return "Placements"

    stem = Path(name).stem
    known = {
        "-mba-business-analytics-ai": "MBA Business Analytics & AI",
        "-mba-business-analytics": "MBA Business Analytics",
        "-mba-financial-services-nse": "MBA Financial Services",
        "-mba-fabm": "MBA-FABM",
        "-mba-oscm": "MBA OSCM",
        "-mba-sm": "MBA SM",
        "-mba-finance": "MBA Finance",
        "-mba-marketing": "MBA Marketing",
        "-mba-hr": "MBA HR",
        "-pgp-finance": "PGP Finance",
        "-pgp-lsm": "PGP LSM",
        "-pgp-bl": "PGP Business Leadership",
        "-pgpba": "PGP Business Analytics",
        "-pgpem": "PGP Enterprise Management",
        "-epgp": "EPGP",
        "-pgpx": "PGPX",
        "-pgdm-financial-management": "PGDM Financial Management",
        "-pgdm-marketing": "PGDM Marketing",
        "-pgdm-retail-management": "PGDM Retail Management",
        "-pgdm-bda": "PGDM Business Analytics",
        "-pgdm-fm": "PGDM Finance",
        "-pgdm-ibm": "PGDM IBM",
        "-pgdm-ib": "PGDM International Business",
        "-pgdm": "PGDM",
        "-fpm": "FPM",
        "-mba-programme": "MBA",
        "-blended-mba-for-working-professionals": "Blended MBA",
        "-executive-mba-hybrid": "Executive MBA",
        "-management-sciences-m-tech": "M.Tech",
        "-management-sciences-phd": "PhD",
        "-btech-ai-data-science": "BTech AI & Data Science",
        "-btech-cse": "BTech CSE",
        "-bba-llb": "BBA LL.B.",
        "-bba": "BBA",
        "-bca": "BCA",
        "-bcom-hons": "BCom (Hons.)",
        "-bcom": "BCom",
        "-mms": "MMS",
        "-mba": "MBA",
    }
    for suffix, text in known.items():
        if stem.endswith(suffix):
            return text
    return stem.replace("-", " ").replace("_", " ").title()

def href_targets(html):
    targets = set()
    for href in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', html, flags=re.I):
        value = href.strip()
        value = re.sub(r'^https?://(?:www\.)?collegedecoded\.in/', '/', value, flags=re.I)
        value = value.split("#", 1)[0].split("?", 1)[0]
        value = value.lstrip("./").lstrip("/")
        if value.endswith(".html"):
            targets.add(value)
        elif value:
            targets.add(value + ".html")
    return targets

def remove_generated_block(html):
    html = re.sub(
        r'<style\b[^>]*id=["\']college-cluster-links-style["\'][^>]*>.*?</style>',
        "",
        html,
        flags=re.I | re.S,
    )
    html = re.sub(
        r'<nav\b[^>]*class=["\'][^"\']*\bcollege-cluster-links\b[^"\']*["\'][^>]*>.*?</nav>',
        "",
        html,
        flags=re.I | re.S,
    )
    return html

def repair(path, members):
    html = path.read_text(encoding="utf-8")
    html = remove_generated_block(html)

    current = href_targets(html)
    missing = [member for member in members if member != path.name and member not in current]
    if not missing:
        path.write_text(html, encoding="utf-8")
        return 0

    links = []
    for member in missing:
        links.append(
            f'<a href="/{member[:-5]}">{label(member, members)}</a>'
        )

    block = (
        '<nav class="college-cluster-links" aria-label="Related college pages">'
        '<strong>Explore related pages</strong>'
        + " · ".join(links)
        + "</nav>"
    )

    body_match = re.search(r"</body>", html, flags=re.I)
    if not body_match:
        return 0

    html = html[:body_match.start()] + block + "\n" + html[body_match.start():]

    if "college-cluster-links-style" not in html:
        head_match = re.search(r"</head>", html, flags=re.I)
        if head_match:
            html = html[:head_match.start()] + STYLE + "\n" + html[head_match.start():]

    path.write_text(html, encoding="utf-8")
    return len(missing)

def main():
    pages = sorted(
        p.name for p in ROOT.glob("*.html")
        if p.name not in {"404.html"}
    )
    clusters = build_clusters(pages)

    changed_pages = 0
    links_added = 0

    for members in clusters.values():
        for name in members:
            if name in EXCLUDED:
                continue
            path = ROOT / name
            if not path.exists():
                continue
            added = repair(path, members)
            if added:
                changed_pages += 1
                links_added += added

    print(
        f"Internal link repair: {links_added} missing reciprocal links "
        f"added across {changed_pages} pages in {len(clusters)} college clusters."
    )

if __name__ == "__main__":
    main()
