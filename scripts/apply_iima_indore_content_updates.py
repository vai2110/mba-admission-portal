from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "iim-indore.html"

SCHOLARSHIP_HTML = '''
<section class="main-section" id="scholarships">
  <h2>Scholarships &amp; Financial Assistance</h2>
  <p>IIM Indore offers Need Based Financial Assistance (NBFA) to admitted PGP, PGP-HRM and IPM participants who need financial support. The institute states that participants with annual family income below ₹12 lakh are eligible to apply; the amount of assistance is not automatic and is decided after assessment of financial need, family income and assets.</p>
  <div class="notice"><strong>What students should know</strong><p>NBFA is financial assistance, not an automatic fee waiver. Eligible students submit the prescribed application and supporting documents. Some applicants may be called for a personal interaction with the NBFA Committee before the award is decided.</p></div>
  <p>The institute also lists merit-linked and other scholarship opportunities. Eligibility, award amount and application requirements can differ by scheme, so students should check the current official notices rather than assume that every scholarship is available to every participant.</p>
  <p><a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-management-pgp/need-based-financial-assistance-nbfa/" target="_blank" rel="noopener">Official NBFA details</a></p>
</section>
'''

FEE_NOTE_HTML = '''
<div class="notice" id="iim-indore-fee-status">
  <strong>Use the 2026–28 fee schedule when budgeting</strong>
  <p>For Indian students entering the PGP 2026–28 batch through CAT, IIM Indore's current fee schedule lists ₹12 lakh course fee for 2026–27 and ₹12 lakh for 2027–28, plus the listed caution deposit, first-year mess deposit and second-year alumni fee. The official PGP programme page separately describes the two-year resident-Indian course fee as ₹24,11,800. These figures should be read with the institute's latest fee schedule rather than older third-party fee figures.</p>
  <p><a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-management-pgp/feestructure/" target="_blank" rel="noopener">Official PGP 2026–28 fee structure</a> &nbsp; <a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-management-pgp/" target="_blank" rel="noopener">Official PGP programme page</a></p>
</div>
'''

PROGRAMME_NOTE_HTML = '''
<div class="notice" id="iim-indore-programme-fee-note">
  <strong>Do not mix programme fees</strong>
  <p>PGP, PGP-HRM and IPM have different fee structures. The PGP-HRM 2026–28 schedule lists ₹10.35 lakh course fee in each academic year, while the PGP/IPM schedule lists ₹12 lakh course fee per year for Indian students. Compare fees only within the programme you are applying to.</p>
  <p><a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-human-resource-management-pgp-hrm/fee-structure/" target="_blank" rel="noopener">Official PGP-HRM 2026–28 fee structure</a> &nbsp; <a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-management-pgp/feestructure/" target="_blank" rel="noopener">Official PGP/IPM 2026–28 fee structure</a></p>
</div>
'''

PLACEMENT_NOTE_HTML = '''
<p class="source-note" id="iim-indore-placement-note"><strong>Placement interpretation:</strong> The placement figures shown on this page describe a reported placement cycle and should be used to understand recent outcomes, not as a guaranteed salary or role for a future batch.</p>
'''


def replace_text(soup, replacements):
    for node in soup.find_all(string=True):
        if node.parent.name in {"script", "style"}:
            continue
        value = str(node)
        new_value = value
        for old, new in replacements.items():
            new_value = new_value.replace(old, new)
        if new_value != value:
            node.replace_with(new_value)


def remove_marker(soup, marker):
    node = soup.find(id=marker)
    if node:
        node.decompose()


def in_hero(node):
    if not node:
        return False
    hero_classes = {"hero", "hero-container", "hero-main", "hero-text"}
    for parent in [node, *node.parents]:
        classes = parent.get("class", []) if getattr(parent, "get", None) else []
        if any(cls in hero_classes for cls in classes):
            return True
    return False


def insert_after_real_section_heading(soup, terms, html, marker):
    """Insert only inside a .main-section; never after hero headings."""
    # If a previous version placed the generated block in the hero, remove it
    # so it can be recreated in the correct section.
    existing = soup.find(id=marker)
    if existing and in_hero(existing):
        existing.decompose()
    elif existing:
        return True

    for section in soup.find_all(["section", "div"], class_=lambda c: c and "main-section" in c):
        heading = section.find(["h2", "h3"], recursive=False)
        if heading and any(term in heading.get_text(" ", strip=True).lower() for term in terms):
            heading.insert_after(BeautifulSoup(html, "html.parser"))
            return True
    return False


def before_section(soup, terms, html, marker):
    existing = soup.find(id=marker)
    if existing and in_hero(existing):
        existing.decompose()
    elif existing:
        return
    for section in soup.find_all(["section", "div"], class_=lambda c: c and "main-section" in c):
        heading = section.find(["h2", "h3"], recursive=False)
        if heading and any(term in heading.get_text(" ", strip=True).lower() for term in terms):
            section.insert_before(BeautifulSoup(html, "html.parser"))
            return


def main():
    soup = BeautifulSoup(PATH.read_text(encoding="utf-8"), "html.parser")

    replace_text(soup, {
        "₹20.70 lakh course fee + ₹50,000 caution + mess*": "₹24.00 lakh course fee across 2026–27 and 2027–28 + listed deposits*",
        "₹20.70 lakh": "₹24.00 lakh (2026–28 course fee)",
        "₹24 lakh+ academic cost": "the current 2026–28 academic cost",
        "This is the number students should use instead of older ₹20–21 lakh figures": "Use the latest official 2026–28 fee schedule rather than older third-party figures",
        "guarantees a high-paying role": "does not by itself guarantee a high-paying role",
        "automatically guarantees a high-paying role": "automatically leads to a high-paying role",
    })

    if not insert_after_real_section_heading(soup, ["fees & roi", "fees and roi", "fees", "cost", "roi"], FEE_NOTE_HTML, "iim-indore-fee-status"):
        raise SystemExit("Could not find a real main-content Fees/Cost/ROI section; refusing to modify the page.")

    if not insert_after_real_section_heading(soup, ["programmes", "courses"], PROGRAMME_NOTE_HTML, "iim-indore-programme-fee-note"):
        raise SystemExit("Could not find a real main-content Programmes/Courses section; refusing to modify the page.")

    before_section(soup, ["faq", "who should apply", "verdict", "student decision", "references", "official sources"], SCHOLARSHIP_HTML, "scholarships")
    if not soup.find(id="scholarships") or in_hero(soup.find(id="scholarships")):
        raise SystemExit("Scholarship section could not be placed outside the hero; refusing to modify the page.")

    remove_marker(soup, "iim-indore-placement-note")
    placement_inserted = False
    for section in soup.find_all(["section", "div"], class_=lambda c: c and "main-section" in c):
        heading = section.find(["h2", "h3"], recursive=False)
        if heading and any(term in heading.get_text(" ", strip=True).lower() for term in ["placements", "career outcomes"]):
            heading.insert_after(BeautifulSoup(PLACEMENT_NOTE_HTML, "html.parser"))
            placement_inserted = True
            break
    if not placement_inserted:
        raise SystemExit("Could not find the real placement section; refusing to place the placement note.")

    for marker in ["iim-indore-fee-status", "iim-indore-programme-fee-note", "iim-indore-placement-note", "scholarships"]:
        node = soup.find(id=marker)
        if in_hero(node):
            raise SystemExit(f"Hero-content safety check failed for #{marker}; refusing to write the page.")

    # No audit-generated notice may exist in the hero.
    hero = soup.select_one(".hero")
    if hero and hero.select(".notice"):
        raise SystemExit("Hero-content safety check failed: notice found inside hero; refusing to write the page.")

    PATH.write_text(str(soup), encoding="utf-8")
    print("Applied reviewed IIM Indore content updates with hero layout protection.")


if __name__ == "__main__":
    main()
