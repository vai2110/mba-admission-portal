from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'iim-indore.html'


def add_after_heading(soup, heading_text, html_fragment):
    for h in soup.find_all(['h2', 'h3']):
        if heading_text.lower() in h.get_text(' ', strip=True).lower():
            node = BeautifulSoup(html_fragment, 'html.parser')
            h.insert_after(node)
            return True
    return False


def main():
    html = PATH.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    # Remove misleading/absolute wording while preserving the underlying admission guidance.
    replacements = {
        'not a guaranteed call or convert': 'not a guarantee of a shortlist or admission',
        'automatically guarantees a high-paying role': 'automatically leads to a high-paying role',
    }
    for old, new in replacements.items():
        for text_node in soup.find_all(string=lambda s: s and old in s):
            text_node.replace_with(text_node.replace(old, new))

    # Make the PGP/PGP-HRM fee distinction explicit so students do not mix programme fees.
    fee_notice = '''
    <div class="notice">
      <strong>Programme fee check — 2026–28</strong>
      <p>IIM Indore's official 2026–28 fee schedule lists the two-year PGP course fee at ₹24,00,000, with a ₹50,000 refundable caution deposit and ₹54,000 first-year mess deposit. The PGP-HRM fee is different: ₹10,35,000 per year, plus the applicable caution/mess and second-year alumni charges. Do not combine PGP and PGP-HRM figures when comparing total cost.</p>
      <p>Fees are based on the institute's published 2026–28 schedules and should be checked again before payment.</p>
      <p><a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-management-pgp/feestructure/" target="_blank" rel="noopener">Official PGP fee structure</a> &nbsp; <a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-human-resource-management-pgp-hrm/fee-structure/" target="_blank" rel="noopener">Official PGP-HRM fee structure</a></p>
    </div>
    '''
    if not soup.find(id='programme-fee-clarity'):
        fee_heading = soup.new_tag('div', id='programme-fee-clarity')
        fee_heading.append(BeautifulSoup(fee_notice, 'html.parser'))
        # Prefer the first fees heading; otherwise place after the programme section.
        inserted = False
        for h in soup.find_all(['h2', 'h3']):
            if 'fees' in h.get_text(' ', strip=True).lower():
                h.insert_after(fee_heading)
                inserted = True
                break
        if not inserted:
            for h in soup.find_all(['h2', 'h3']):
                if 'program' in h.get_text(' ', strip=True).lower():
                    h.insert_after(fee_heading)
                    inserted = True
                    break

    # Add a student-useful scholarship section using current official IIM Indore policy.
    scholarship_html = '''
    <section class="main-section" id="scholarships">
      <h2>Scholarships &amp; Financial Assistance</h2>
      <p>IIM Indore offers Need Based Financial Assistance (NBFA) for participants who need financial support. The institute states that admitted PGP, PGP-HRM and IPM students with annual family income below ₹12 lakh can apply, with the final assistance determined after assessment of family income, assets and other relevant factors.</p>
      <div class="notice">
        <strong>What students should know</strong>
        <p>NBFA is not an automatic fee waiver. Applicants submit financial information and supporting documents, and some applicants may be called for a personal interaction with the NBFA Committee. The amount of assistance is decided by the institute on a year-to-year basis.</p>
      </div>
      <p>IIM Indore also administers merit-linked awards and other scholarships. Eligibility and award amounts vary by scheme, so students should check the latest institute communication after admission rather than assuming that a particular award will be available to every student.</p>
      <p><a class="source-link" href="https://iimidr.ac.in/programmes/academic-programmes/post-graduate-programme-in-management-pgp/need-based-financial-assistance-nbfa/" target="_blank" rel="noopener">Official NBFA details</a> &nbsp; <a class="source-link" href="https://iimidr.ac.in/wp-content/uploads/2025/11/Admission-Procedure-PGP-2026-28-Batch.pdf" target="_blank" rel="noopener">PGP 2026–28 admission procedure</a></p>
    </section>
    '''
    if not soup.find(id='scholarships'):
        scholarship = BeautifulSoup(scholarship_html, 'html.parser')
        inserted = False
        for h in soup.find_all('h2'):
            if any(x in h.get_text(' ', strip=True).lower() for x in ['references', 'official sources', 'student discussions']):
                h.parent.insert_before(scholarship)
                inserted = True
                break
        if not inserted:
            content = soup.find('main') or soup.body
            content.append(scholarship)

    # Strengthen the thin references section without adding generic filler.
    for h in soup.find_all('h2'):
        if 'references' in h.get_text(' ', strip=True).lower() or 'official sources' in h.get_text(' ', strip=True).lower():
            p = h.find_next('p')
            if p and len(p.get_text(' ', strip=True)) < 250:
                p.insert_after(BeautifulSoup('<p>Use the official institute pages for the latest admission procedure, fee schedule, financial assistance rules and placement reports. Third-party discussions can help with context, but should not override institute-published facts.</p>', 'html.parser'))
            break

    PATH.write_text(str(soup), encoding='utf-8')
    print('Applied reviewed IIM Indore content updates.')


if __name__ == '__main__':
    main()
