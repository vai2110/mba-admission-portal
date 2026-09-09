import re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"iim-ahmedabad.html", "sibm-pune.html", "404.html", "content-audit.html", "college-page-audit-dashboard.html", "github-direct-edit-test.html", "irma-deploy-trigger.html"}
NAV_CSS = """
.college-cluster-nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 18px;padding:10px 12px;background:#f8fbff;border:1px solid #dbe7f5;border-radius:8px;font-size:11px;line-height:1.4}.college-cluster-nav strong{color:#173f82;font-size:11px;margin-right:2px}.college-cluster-nav a{color:#2563eb!important;font-weight:700;text-decoration:none}.college-cluster-nav a:hover{text-decoration:underline}.college-cluster-nav .sep{color:#94a3b8}
""".strip()


def build_clusters(pages):
    names = set(pages)
    clusters = {}
    for placement in sorted(n for n in pages if n.endswith("-placements.html")):
        base = placement[:-len("-placements.html")] + ".html"
        if base not in names:
            continue
        prefix = base[:-5]
        programmes = sorted(n for n in pages if n not in {base, placement} and n.startswith(prefix + "-"))
        clusters[base] = [base, *programmes, placement]
    return clusters


def label(name):
    stem = Path(name).stem
    if stem.endswith("-placements"):
        return "Placements"
    if stem.endswith("-mba"):
        return "MBA"
    if stem.endswith("-pgdm"):
        return "PGDM"
    if stem.endswith("-mms"):
        return "MMS"
    if stem.endswith("-btech-cse"):
        return "BTech CSE"
    if stem.endswith("-btech-ai-data-science"):
        return "BTech AI & Data Science"
    if stem.endswith("-bba"):
        return "BBA"
    if stem.endswith("-bca"):
        return "BCA"
    if stem.endswith("-bcom"):
        return "BCom"
    if stem.endswith("-mba-business-analytics"):
        return "MBA Business Analytics"
    if stem.endswith("-mba-finance"):
        return "MBA Finance"
    if stem.endswith("-mba-marketing"):
        return "MBA Marketing"
    if stem.endswith("-mba-hr"):
        return "MBA HR"
    if stem.endswith("-pgpba"):
        return "PGPBA"
    if stem.endswith("-pgpx"):
        return "PGPX"
    return "Programme"


def add_nav(path, members):
    if path.name in EXCLUDED:
        return False
    text = path.read_text(encoding="utf-8")
    if 'class="college-cluster-nav"' in text:
        return False
    soup = BeautifulSoup(text, "html.parser")
    main = soup.find("main")
    if not main:
        return False
    overview = members[0]
    links = []
    for member in members:
        if member == path.name:
            continue
        links.append(f'<a href="{member}">{label(member)}</a>')
    nav_html = '<nav class="college-cluster-nav" aria-label="College page navigation"><strong>Explore this college</strong><span class="sep">|</span>' + '<span class="sep">|</span>'.join(links) + '</nav>'
    nav = BeautifulSoup(nav_html, "html.parser").nav
    main.insert(0, nav)
    style = soup.find("style")
    if style and ".college-cluster-nav" not in style.get_text():
        style.append("\n" + NAV_CSS + "\n")
    path.write_text(str(soup), encoding="utf-8")
    return True


def main():
    pages = sorted(p.name for p in ROOT.glob("*.html"))
    clusters = build_clusters(pages)
    changed = []
    for members in clusters.values():
        for member in members:
            path = ROOT / member
            if add_nav(path, members):
                changed.append(member)
    print(f"Phase 3 reciprocal navigation: updated {len(changed)} pages across {len(clusters)} detected college clusters.")
    for name in changed:
        print(name)


if __name__ == "__main__":
    main()
