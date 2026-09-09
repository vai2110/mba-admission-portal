import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    "iim-ahmedabad.html", "sibm-pune.html", "404.html", "content-audit.html",
    "college-page-audit-dashboard.html", "github-direct-edit-test.html", "irma-deploy-trigger.html",
    "welingkar-mumbai-links.html", "welingkar-mumbai-programmes-note.html", "welingkar-mumbai-programmes.html",
    "mica.html", "mica-pgdm-c.html", "mica-pgdm.html", "mica-placements.html"
}
MICA_PAGES = {"mica.html", "mica-pgdm-c.html", "mica-pgdm.html", "mica-placements.html"}
NAV_CSS = ".college-cluster-nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 18px;padding:10px 12px;background:#f8fbff;border:1px solid #dbe7f5;border-radius:8px;font-size:11px;line-height:1.4}.college-cluster-nav strong{color:#173f82;font-size:11px;margin-right:2px}.college-cluster-nav a{color:#2563eb!important;font-weight:700;text-decoration:none}.college-cluster-nav a:hover{text-decoration:underline}.college-cluster-nav .sep{color:#94a3b8}"

ALIAS_CLUSTERS = {
    "iim-nagpur.html": ["iim-nagpur.html", "indian-institute-of-management-nagpur-mba.html", "indian-institute-of-management-nagpur-blended-mba-for-working-professionals.html", "indian-institute-of-management-nagpur-executive-mba-hybrid.html", "iim-nagpur-placements.html"],
    "iit-kanpur.html": ["iit-kanpur.html", "indian-institute-of-technology-kanpur-mba-programme.html", "iit-kanpur-management-sciences-m-tech.html", "iit-kanpur-management-sciences-phd.html", "iit-kanpur-placements.html"],
    "jaipuria-institute-of-management-lucknow.html": ["jaipuria-institute-of-management-lucknow.html", "jaipuria-lucknow-fpm.html", "jaipuria-lucknow-pgdm.html", "jaipuria-lucknow-pgdm-financial-services.html", "jaipuria-lucknow-pgdm-retail-management.html", "jaipuria-institute-of-management-lucknow-placements.html"],
}

def build_clusters(pages):
    names = set(pages); clusters = {}
    for placement in sorted(n for n in pages if n.endswith("-placements.html")):
        base = placement[:-len("-placements.html")] + ".html"
        if base not in names: continue
        prefix = base[:-5]
        programmes = sorted(n for n in pages if n not in {base, placement} and n not in EXCLUDED and n.startswith(prefix + "-"))
        clusters[base] = [base, *programmes, placement]
    for overview, members in ALIAS_CLUSTERS.items():
        if overview not in names: continue
        valid = [m for m in members if m in names and m not in EXCLUDED]
        if len(valid) >= 2: clusters[overview] = valid
    return clusters

def label(name):
    stem = Path(name).stem
    if stem.endswith("-placements"): return "Placements"
    known = {"-mba-business-analytics-ai":"Business Analytics & AI","-mba-business-analytics":"MBA Business Analytics","-mba-financial-services-nse":"MBA Financial Services","-mba-fabm":"MBA-FABM","-mba-oscm":"MBA OSCM","-mba-sm":"MBA SM","-mba-finance":"MBA Finance","-mba-marketing":"MBA Marketing","-mba-hr":"MBA HR","-pgp-finance":"PGP Finance","-pgp-lsm":"PGP LSM","-pgp-bl":"PGP Business Leadership","-pgpba":"PGP Business Analytics","-pgpem":"PGP Enterprise Management","-epgp":"EPGP","-pgpx":"PGPX","-pgdm-financial-management":"PGDM Financial Management","-pgdm-marketing":"PGDM Marketing","-pgdm-retail-management":"PGDM Retail Management","-pgdm-bda":"PGDM Business Analytics","-pgdm-fm":"PGDM Finance","-pgdm-ibm":"PGDM IBM","-pgdm-ib":"PGDM International Business","-pgdm":"PGDM","-fpm":"FPM","-mba-programme":"MBA","-blended-mba-for-working-professionals":"Blended MBA","-executive-mba-hybrid":"Executive MBA","-management-sciences-m-tech":"M.Tech","-management-sciences-phd":"PhD","-btech-ai-data-science":"BTech AI & Data Science","-btech-cse":"BTech CSE","-bba-llb":"BBA LL.B.","-bba":"BBA","-bca":"BCA","-bcom-hons":"BCom (Hons.)","-bcom":"BCom","-mms":"MMS","-mba":"MBA"}
    for suffix, text in known.items():
        if stem.endswith(suffix): return text
    return stem.split("-")[-1].replace("_", " ").title()

def nav_html(current, members):
    links = []
    for member in members:
        if member != current: links.append(f'<a href="{member}">{"Overview" if member == members[0] else label(member)}</a>')
    return '<nav class="college-cluster-nav" aria-label="College page navigation"><strong>Explore this college</strong><span class="sep">|</span>' + '<span class="sep">|</span>'.join(links) + '</nav>'

def remove_mica_nav(path):
    text = path.read_text(encoding="utf-8")
    pattern = r'<nav\b[^>]*class=["\'][^"\']*\bcollege-cluster-nav\b[^"\']*["\'][^>]*>.*?</nav>'
    updated = re.sub(pattern, "", text, count=1, flags=re.I | re.S)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False

def repair(path, members):
    if path.name in EXCLUDED: return False
    text = path.read_text(encoding="utf-8"); replacement = nav_html(path.name, members)
    pattern = r'<nav\b[^>]*class=["\'][^"\']*\bcollege-cluster-nav\b[^"\']*["\'][^>]*>.*?</nav>'
    if re.search(pattern, text, flags=re.I | re.S):
        without_nav = re.sub(pattern, "", text, count=1, flags=re.I | re.S)
        updated = re.sub(r'(<body\b[^>]*>)', r'\1' + replacement, without_nav, count=1, flags=re.I)
        if updated == without_nav: updated = re.sub(r'(<main\b[^>]*>)', r'\1' + replacement, without_nav, count=1, flags=re.I)
    else:
        updated = re.sub(r'(<body\b[^>]*>)', r'\1' + replacement, text, count=1, flags=re.I)
        if updated == text: updated = re.sub(r'(<main\b[^>]*>)', r'\1' + replacement, text, count=1, flags=re.I)
    if ".college-cluster-nav" not in updated: updated = re.sub(r'</style>', NAV_CSS + '</style>', updated, count=1, flags=re.I)
    if updated != text: path.write_text(updated, encoding="utf-8"); return True
    return False

def main():
    pages = sorted(p.name for p in ROOT.glob("*.html")); changed = []
    for name in sorted(MICA_PAGES):
        path = ROOT / name
        if path.exists() and remove_mica_nav(path): changed.append(name)
    for members in build_clusters(pages).values():
        for member in members:
            if repair(ROOT / member, members): changed.append(member)
    print(f"Phase 3 v2: repaired {len(changed)} college pages.")
    for name in changed: print(name)

if __name__ == "__main__": main()
