import json
import re
from pathlib import Path
from urllib.parse import urlparse

DATA = Path('mba-cutoff-data.json')

# Known abbreviations whose page filenames are not a literal slug of the display name.
ALIASES = {
    'scmhrd pune': 'scmhrd-pune.html',
    'siib pune': 'siib-pune.html',
    'sibm bengaluru': 'sibm-bengaluru.html',
    'siom nashik': 'siom-nashik.html',
    'sitm pune': 'sitm-pune.html',
    'sibm nagpur': 'sibm-nagpur.html',
    'sicsr pune': 'sicsr-pune.html',
    'sims pune': 'sims-pune.html',
    'scit pune': 'scit-pune.html',
}

def norm(value):
    return re.sub(r'[^a-z0-9]+', '-', str(value).lower()).strip('-')


data = json.loads(DATA.read_text(encoding='utf-8'))
files = {p.name for p in Path('.').glob('*.html')}
changed = []
remaining_external = []

for exam, block in data.get('exams', {}).items():
    for row in block.get('rows', []):
        page = str(row.get('page', '')).strip()
        if not page or not urlparse(page).scheme:
            continue

        college = str(row.get('college', '')).strip()
        candidates = []
        if college.lower() in ALIASES:
            candidates.append(ALIASES[college.lower()])
        candidates.append(norm(college) + '.html')

        # Try common punctuation/name variants before leaving an external URL intact.
        simplified = re.sub(r'\b(the|institute|of|management|business|school|university)\b', '', college.lower())
        candidates.append(norm(simplified) + '.html')

        local = next((c for c in candidates if c in files), None)
        if local:
            changed.append((college, page, local))
            row['page'] = local
        else:
            remaining_external.append((college, page))

DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(f'Repaired {len(changed)} cutoff page links.')
for college, old, new in changed:
    print(f'  {college}: {old} -> {new}')
print(f'External links retained because no matching local page exists: {len(remaining_external)}')
for college, page in remaining_external:
    print(f'  {college}: {page}')
