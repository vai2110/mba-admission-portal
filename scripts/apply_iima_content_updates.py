from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "iim-ahmedabad.html"

SCHOLARSHIP_HTML = '''
<section class="main-section" id="scholarships">
  <h2>Scholarships &amp; Financial Assistance</h2>
  <p>IIM Ahmedabad provides need-based financial assistance for students in the two-year PGP and PGP-FABM programmes. The institute states that scholarship decisions consider factors such as annual gross family income, family assets and the number of dependants. Applications for the Special Need Based Scholarship are invited each year, with the current admission page directing students to the institute's financial-assistance process.</p>
  <div class="notice">
    <strong>What this means for applicants</strong>
    <p>Do not treat a scholarship as an automatic fee waiver. Financial assistance is assessed individually, so students should evaluate their family finances and education-loan requirement before assuming that a particular amount will be awarded.</p>
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


def main():
    html = PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Remove the duplicate occurrence of the exact sentence while retaining one useful occurrence.
    sentence = "IIMA's PGP includes both fresh graduates and candidates with prior work experience."
    matches = soup.find_all(string=lambda s: s and sentence in s)
    if len(matches) > 1:
        for node in matches[1:]:
            node.replace_with(node.replace(sentence, ""))

    # Remove the four promotional/absolute formulations flagged by the free audit.
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

    # Add a decision-useful scholarship section if it is not already present.
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

    PATH.write_text(str(soup), encoding="utf-8")


if __name__ == "__main__":
    main()
