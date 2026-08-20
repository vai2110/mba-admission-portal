from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "iim-ahmedabad.html"

SCHOLARSHIP_HTML = '''
<section class="main-section" id="scholarships">
  <h2>Scholarships &amp; Financial Assistance</h2>
  <p>IIM Ahmedabad provides need-based financial assistance for students in the two-year PGP and PGP-FABM programmes. The institute states that scholarship decisions consider factors such as annual gross family income, family assets and the number of dependants. Applications for the need-based scholarship process are invited each year.</p>
  <div class="notice">
    <strong>What this means for applicants</strong>
    <p>A scholarship should not be treated as an automatic fee waiver. Financial assistance is assessed individually, so students should consider their family finances and education-loan requirement before assuming that a particular amount will be awarded.</p>
  </div>
  <div class="table-wrapper">
    <table>
      <thead><tr><th>Assistance route</th><th>What students should know</th></tr></thead>
      <tbody>
        <tr><td>IIMA Need-Based Scholarship</td><td>Financial assistance is assessed using financial circumstances such as family income, assets and dependants.</td></tr>
        <tr><td>Alumni / industry scholarships</td><td>IIMA also lists scholarships supported by alumni, industry and other donors; eligibility and award amounts vary by scheme.</td></tr>
        <tr><td>Government scholarships</td><td>Eligible students can also explore applicable Government of India scholarship schemes through the relevant official portals.</td></tr>
      </tbody>
    </table>
  </div>
  <p class="source-note"><strong>Source:</strong> <a href="https://www.iima.ac.in/academics/mba/admissions/indians" target="_blank" rel="noopener">IIMA MBA admission page</a> and <a href="https://www.iima.ac.in/sites/default/files/2024-06/Point%2013%20Rules%20and%20Regulations%20for%20Financial%20AssistanceScholarships.pdf" target="_blank" rel="noopener">IIMA scholarship rules</a>.</p>
</section>
'''

FEE_NOTE_HTML = '''
<div class="notice iima-verified-note" id="fee-status-note">
  <strong>Fee status for 2026–28</strong>
  <p>IIMA currently publishes a PGP programme fee of ₹27.50 lakh for the 2025–27 batch, including ₹20.10 lakh in tuition fees. The institute states that fees for future batches will be announced later, so the 2025–27 figure should not be presented as the confirmed 2026–28 fee.</p>
  <p class="source-note"><strong>Source:</strong> <a href="https://www.iima.ac.in/academics/mba/admissions/indians" target="_blank" rel="noopener">IIMA PGP admission page</a>.</p>
</div>
'''

PLACEMENT_NOTE_HTML = '''
<p class="source-note" id="placement-source-note"><strong>Placement data source:</strong> IIMA's 2025 IPRS report lists a median salary of ₹34.59 LPA and mean salary of ₹35.50 LPA for the MBA-PGP. These figures describe the reported placement outcome for that cycle; they should not be presented as a guaranteed salary for future batches.</p>
'''


def remove_duplicate_sentence(soup, sentence):
    """Remove duplicate occurrences without leaving broken paragraphs or table cells."""
    occurrences = []
    for tag in soup.find_all(["p", "li", "td", "th", "div"]):
        if sentence in tag.get_text(" ", strip=True):
            occurrences.append(tag)
    if len(occurrences) <= 1:
        return
    for tag in occurrences[1:]:
        text = tag.get_text(" ", strip=True)
        if text == sentence:
            tag.decompose()
        else:
            # Remove only the duplicate sentence if the block contains other useful text.
            for node in list(tag.find_all(string=lambda s: s and sentence in s)):
                node.replace_with(str(node).replace(sentence, "").strip())


def add_after_heading(soup, heading_text, html, element_id):
    if soup.find(id=element_id):
        return
    for heading in soup.find_all(["h2", "h3"]):
        if heading.get_text(" ", strip=True).lower() == heading_text.lower():
            parent = heading.parent
            if parent:
                block = BeautifulSoup(html, "html.parser")
                # Put the verified note immediately after the heading's section heading.
                heading.insert_after(block)
                return


def main():
    html = PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove the duplicate PGP work-experience sentence robustly.
    sentence = "IIMA's PGP includes both fresh graduates and candidates with prior work experience."
    remove_duplicate_sentence(soup, sentence)

    # 2. Remove only genuinely promotional formulations. Do not rewrite cautionary statements.
    replacements = {
        "one of the best": "among the most selective",
        "best college": "the institute",
        "dream college": "the institute",
        "unmatched": "broad",
        "unparalleled": "strong",
        "guarantees a call": "does not by itself determine an interview call",
        "guarantee an interview call": "by itself determine an interview call",
        "does not guarantee a specific company, function or salary": "does not determine a specific company, function or salary",
    }
    for text_node in soup.find_all(string=True):
        if text_node.parent.name in {"script", "style"}:
            continue
        value = str(text_node)
        new_value = value
        for old, new in replacements.items():
            new_value = new_value.replace(old, new).replace(old.title(), new)
        if new_value != value:
            text_node.replace_with(new_value)

    # 3. Add scholarship guidance if missing.
    if not soup.find(id="scholarships"):
        anchor = None
        for tag in soup.find_all(["section", "div"]):
            heading = tag.find(["h2", "h3"], recursive=False)
            if heading and "who should apply" in heading.get_text(" ", strip=True).lower():
                anchor = tag
                break
        if anchor is None:
            for tag in soup.find_all(["section", "div"]):
                heading = tag.find(["h2", "h3"], recursive=False)
                if heading and "faq" in heading.get_text(" ", strip=True).lower():
                    anchor = tag
                    break
        new_section = BeautifulSoup(SCHOLARSHIP_HTML, "html.parser")
        if anchor:
            anchor.insert_before(new_section)
        else:
            content = soup.find(class_="content") or soup.body
            content.append(new_section)

    # 4. Add a clearly labelled fee-status note near the Fees & ROI section.
    if not soup.find(id="fee-status-note"):
        for heading in soup.find_all(["h2", "h3"]):
            if "fees & roi" in heading.get_text(" ", strip=True).lower():
                block = BeautifulSoup(FEE_NOTE_HTML, "html.parser")
                heading.insert_after(block)
                break

    # 5. Add a source-aware placement interpretation without changing the reported figures.
    if not soup.find(id="placement-source-note"):
        for heading in soup.find_all(["h2", "h3"]):
            if "placements & career outcomes" in heading.get_text(" ", strip=True).lower():
                block = BeautifulSoup(PLACEMENT_NOTE_HTML, "html.parser")
                # Insert after the first paragraph/card content under this heading's section.
                section = heading.parent
                if section:
                    section.append(block)
                break

    PATH.write_text(str(soup), encoding="utf-8")


if __name__ == "__main__":
    main()
