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


def after_heading(soup, terms, html, marker):
    if soup.find(id=marker):
        return
    for heading in soup.find_all(["h2", "h3"]):
        text = heading.get_text(" ", strip=True).lower()
        if any(term in text for term in terms):
            heading.insert_after(BeautifulSoup(html, "html.parser"))
            return


def before_section(soup, terms, html, marker):
    if soup.find(id=marker):
        return
    for section in soup.find_all(["section", "div"]):
        heading = section.find(["h2", "h3"], recursive=False)
        if heading and any(term in heading.get_text(" ", strip=True).lower() for term in terms):
            section.insert_before(BeautifulSoup(html, "html.parser"))
            return


def main():
    soup = BeautifulSoup(PATH.read_text(encoding="utf-8"), "html.parser")

    # Remove obsolete/ambiguous legacy fee wording where it appears in the article.
    replace_text(soup, {
        "₹20.70 lakh course fee + ₹50,000 caution + mess*": "₹24.00 lakh course fee across 2026–27 and 2027–28 + listed deposits*",
        "₹20.70 lakh": "₹24.00 lakh (2026–28 course fee)",
        "₹24 lakh+ academic cost": "the current 2026–28 academic cost",
        "This is the number students should use instead of older ₹20–21 lakh figures": "Use the latest official 2026–28 fee schedule rather than older third-party figures",
        "guarantees a high-paying role": "does not by itself guarantee a high-paying role",
        "automatically guarantees a high-paying role": "automatically leads to a high-paying role",
    })

    after_heading(soup, ["fees & roi", "fees and roi", "fees"], FEE_NOTE_HTML, "iim-indore-fee-status")
    after_heading(soup, ["programmes", "courses"], PROGRAMME_NOTE_HTML, "iim-indore-programme-fee-note")
    before_section(soup, ["faq", "who should apply", "verdict", "student decision", "references", "official sources"], SCHOLARSHIP_HTML, "scholarships")
    after_heading(soup, ["placements & career outcomes", "placements", "career outcomes"], PLACEMENT_NOTE_HTML, "iim-indore-placement-note")

    PATH.write_text(str(soup), encoding="utf-8")
    print("Applied reviewed IIM Indore content updates.")


if __name__ == "__main__":
    main()
