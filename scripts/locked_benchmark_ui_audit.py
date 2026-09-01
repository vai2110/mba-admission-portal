import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'index.html','404.html','content-audit.html','college-page-audit-dashboard.html'}

H2_REPLACEMENTS = {
    'IIT Roorkee Management Studies: What Students Can Study': 'IIT Roorkee MBA & Executive MBA',
    'IIT Roorkee MBA & Executive MBA: Which Route Fits You?': 'IIT Roorkee MBA vs Executive MBA',
    'IIT Roorkee MBA Admission Process': 'IIT Roorkee MBA Admission Process',
    'IIT Roorkee MBA Placements: Latest Highlights': 'IIT Roorkee MBA Placement Highlights',
    'IIT Roorkee MBA Placements 2025: Latest Highlights': 'IIT Roorkee MBA Placement Highlights',
    'IIT Roorkee MBA Placement Reports: 2025 and Earlier': 'IIT Roorkee MBA Placement Trends',
    'Roles and Sectors in IIT Roorkee MBA Placements': 'IIT Roorkee MBA Placement Roles',
    'IIT Roorkee MBA Summer Placements: 2024-26 Batch': 'IIT Roorkee MBA Summer Placements',
    'How Students Should Read IIT Roorkee Placement Data': 'How to Read IIT Roorkee Placement Data',
    'IIT Roorkee Executive MBA: What the Programme Is': 'IIT Roorkee Executive MBA Overview',
    'Executive MBA Programme Structure & Specialisations': 'IIT Roorkee Executive MBA Structure',
    'How the IIT Roorkee Executive MBA Is Delivered': 'IIT Roorkee Executive MBA Format',
    'IIT Roorkee Executive MBA: What Students Receive': 'IIT Roorkee Executive MBA Benefits',
}


def compact_css(soup):
    changed = False
    for style in soup.find_all('style'):
        css = style.string or style.get_text()
        new = css
        new = re.sub(r'(\.hero\{[^}]*?)padding:28px 0', r'\1padding:18px 0', new)
        new = re.sub(r'(\.hero h1\{[^}]*?)font-size:31px', r'\1font-size:26px', new)
        new = re.sub(r'(\.hero p\{[^}]*?)font-size:13px', r'\1font-size:12px', new)
        new = re.sub(r'(\.hero p\{[^}]*?)max-width:900px', r'\1max-width:760px', new)
        new = re.sub(r'(\.facts\{[^}]*?margin:)16px auto', r'\112px auto', new)
        new = re.sub(r'(\.fact,.sec,.ans\{[^}]*?)padding:17px', r'\1padding:14px', new)
        new = re.sub(r'(\.sec h2\{[^}]*?)font-size:21px', r'\1font-size:18px', new)
        new = re.sub(r'(\.sec h2\{[^}]*?)padding-bottom:8px', r'\1padding-bottom:6px', new)
        if new != css:
            style.string = new
            changed = True
    return changed


def remove_duplicate_quick_answer(soup):
    blocks = soup.select('.answer-first')
    changed = False
    for block in blocks:
        block.decompose()
        changed = True
    for style in soup.find_all('style'):
        css = style.string or style.get_text()
        new = re.sub(r'\.answer-first\{[^}]*\}\.answer-first strong\{[^}]*\}\.answer-first p\{[^}]*\}', '', css)
        if new != css:
            style.string = new
            changed = True
    return changed


def shorten_h2s(soup):
    changed = False
    for h2 in soup.find_all('h2'):
        old = h2.get_text(' ', strip=True)
        new = H2_REPLACEMENTS.get(old)
        if new and new != old:
            h2.string = new
            changed = True
    return changed


def ensure_hr_between_sections(soup):
    main = soup.find('main')
    if not main:
        return False
    changed = False
    sections = [x for x in main.find_all('section', recursive=False)]
    for section in sections[1:]:
        prev = section.previous_sibling
        while prev is not None and getattr(prev, 'name', None) is None and not str(prev).strip():
            prev = prev.previous_sibling
        if getattr(prev, 'name', None) != 'hr':
            hr = soup.new_tag('hr')
            section.insert_before(hr)
            changed = True
    return changed


def fix_file(path):
    raw = path.read_text(encoding='utf-8')
    soup = BeautifulSoup(raw, 'html.parser')
    changed = False
    changes = []
    if remove_duplicate_quick_answer(soup): changes.append('removed duplicate answer-first Quick Answer block') ; changed = True
    if compact_css(soup): changes.append('tightened hero, facts and H2 sizing to compact SIBM Pune-style proportions') ; changed = True
    if shorten_h2s(soup): changes.append('shortened and keyword-optimised search-intent H2s') ; changed = True
    if ensure_hr_between_sections(soup): changes.append('ensured hr separation between consecutive main sections') ; changed = True
    if changed:
        path.write_text(str(soup), encoding='utf-8')
    return path.name, changed, changes


def main():
    raw_targets = os.environ.get('TARGET_PAGES','').strip()
    names = [x.strip() for x in raw_targets.splitlines() if x.strip()] if raw_targets else [p.name for p in ROOT.glob('*.html')]
    results=[]
    for name in names:
        path=(ROOT/name).resolve()
        if path.parent != ROOT or path.suffix.lower() != '.html' or not path.exists() or path.name in EXCLUDED or path.name.startswith('sibm-pune') or path.name.startswith('iim-ahmedabad'):
            continue
        results.append(fix_file(path))
    print({'pages_checked':len(results),'pages_changed':sum(x[1] for x in results),'results':results})

if __name__=='__main__': main()
