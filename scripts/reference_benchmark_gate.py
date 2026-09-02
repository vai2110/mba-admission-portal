import csv, json, os, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'data/college-production-state.json'
QUEUE = ROOT / 'data/college-queue.csv'
REPORT = ROOT / 'reference-benchmark-audit.json'
MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')
DONE = 'Created + Audited'

# These are the locked production standards distilled from the six reference pages:
# content-depth benchmark (IIM Ahmedabad), architecture/design benchmark (SIBM Pune),
# plus the remaining reference set's shared requirements: student intent, source discipline,
# mobile-first hierarchy, decision aids and programme-level completeness.
COMMON = [
    ('identity', ['overview', 'about', 'history', 'established']),
    ('admission', ['admission', 'application', 'apply', 'selection', 'shortlist']),
    ('eligibility', ['eligibility', 'eligible', 'qualification']),
    ('exam', ['cat', 'xat', 'gmat', 'nmat', 'snap', 'entrance', 'exam']),
    ('cutoff', ['cutoff', 'cut-off', 'percentile', 'screening']),
    ('fees', ['fee', 'fees', 'tuition', 'total cost']),
    ('programmes', ['programme', 'program', 'course']),
    ('placements', ['placement', 'placements', 'salary', 'ctc', 'recruiter']),
    ('faqs', ['faq', 'frequently asked']),
    ('official_sources', ['official sources', 'official website', 'source']),
]
OVERVIEW = COMMON + [
    ('rankings', ['ranking', 'nirf']),
    ('selection_logic', ['selection criteria', 'selection process', 'weight', 'composite']),
    ('dates', ['important dates', 'deadline', 'schedule', 'last date']),
    ('student_profile', ['batch profile', 'student profile', 'class profile', 'work experience']),
    ('student_life', ['student life', 'campus life', 'clubs', 'community', 'campus']),
    ('scholarships', ['scholarship', 'financial aid', 'fee waiver']),
    ('fit', ['who should', 'who can apply', 'fit', 'suitable', 'consider']),
]
PLACEMENT = [
    ('placement_overview', ['placement', 'career outcomes']),
    ('latest_metrics', ['average', 'median', 'highest', 'ctc', 'lpa']),
    ('yearwise_trend', ['2025', '2024', '2023', 'trend', 'year-wise', 'year wise']),
    ('recruiters', ['recruiter', 'companies', 'organizations']),
    ('sectors', ['sector', 'industry']),
    ('roles', ['role', 'roles', 'function', 'profile']),
    ('summer', ['summer internship', 'internship', 'stipend']),
    ('how_to_read', ['how to read', 'interpret', 'should students']),
    ('official_sources', ['official sources', 'placement report', 'official website']),
    ('faqs', ['faq', 'frequently asked']),
]
COURSE = COMMON + [
    ('course_overview', ['programme overview', 'program overview', 'duration', 'full-time', 'weekend']),
    ('selection_logic', ['selection criteria', 'selection process', 'shortlist', 'weight']),
    ('curriculum', ['curriculum', 'course structure', 'trimesters', 'semester', 'subjects']),
    ('specialisations', ['specialisation', 'specialization', 'major', 'elective']),
    ('career_outcomes', ['career', 'roles', 'recruiters', 'placements']),
    ('fit', ['who should', 'fit', 'suitable', 'freshers', 'work experience']),
]


def load_state():
    return json.loads(STATE.read_text(encoding='utf-8'))

def college_for_page(name, state):
    for rank, rec in state.get('colleges', {}).items():
        for key in ('Overview Page','Placement Page','Course Page 1','Course Page 2','Course Page 3'):
            if rec.get(key) == 'Created — Audit Pending' or rec.get(key) == DONE:
                if name == rec.get('course_filenames', [None,None,None])[0] or name == rec.get('course_filenames', [None,None,None])[1] or name == rec.get('course_filenames', [None,None,None])[2]:
                    return int(rank), rec
        # fallback for overview/placement filenames
        try:
            with QUEUE.open(encoding='utf-8-sig', newline='') as f: rows=list(csv.DictReader(f))
            row=next((x for x in rows if str(x['rank'])==str(rank)),None)
            if row:
                base=re.sub(r'[^a-z0-9]+','-',row['college_name'].lower()).strip('-')
                if name in (f'{base}.html', f'{base}-placements.html'):
                    return int(rank), rec
        except Exception: pass
    return None, None

def page_kind(filename, rec):
    if filename.endswith('-placements.html'): return 'placement'
    if filename in rec.get('course_filenames', []): return 'course'
    return 'overview'

def clean(soup):
    clone=BeautifulSoup(str(soup),'html.parser')
    for t in clone(['script','style','noscript','svg','nav','header','footer']): t.decompose()
    return re.sub(r'\s+',' ',clone.get_text(' ',strip=True)).lower()

def audit_file(path, kind):
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    text=clean(soup)
    req = OVERVIEW if kind=='overview' else PLACEMENT if kind=='placement' else COURSE
    missing=[name for name, terms in req if not any(term in text for term in terms)]
    h2s=[h.get_text(' ',strip=True) for h in soup.find_all('h2')]
    hr_ok=True
    main=soup.find('main')
    if main:
        sections=[x for x in main.find_all('section',recursive=False)]
        for sec in sections[1:]:
            prev=sec.previous_sibling
            while prev is not None and getattr(prev,'name',None) is None and not str(prev).strip(): prev=prev.previous_sibling
            if getattr(prev,'name',None)!='hr': hr_ok=False; break
    architecture = {
        'quick_answer': bool(soup.select_one('.answer, .quick-answer, [class*="answer"]')),
        'on_this_page': 'on this page' in text or bool(soup.select_one('[aria-label*="On This Page"], nav a[href^="#"]')),
        'h2_count': len(h2s),
        'hr_between_sections': hr_ok,
        'tables_or_cards': bool(soup.find('table') or soup.select_one('.card,.cards,.grid,.fact,.facts')),
        'internal_links': sum(1 for a in soup.find_all('a',href=True) if not a['href'].startswith(('http://','https://','#','mailto:'))),
    }
    design = {
        'viewport': bool(soup.find('meta',attrs={'name':'viewport'})),
        'shared_css': bool(any('college-page.css' in (l.get('href') or '') for l in soup.find_all('link',href=True))),
        'compact_hero': bool(soup.select_one('.hero')),
        'responsive_css': '@media' in ''.join((s.get_text() or '') for s in soup.find_all('style')) or bool(soup.find('link',href=lambda x: x and 'college-page.css' in x)),
        'single_h1': len(soup.find_all('h1'))==1,
    }
    arch_fail=[]
    if not architecture['quick_answer']: arch_fail.append('Quick Answer/answer box')
    if not architecture['on_this_page']: arch_fail.append('On This Page navigation')
    if architecture['h2_count'] < (8 if kind=='overview' else 7 if kind=='course' else 6): arch_fail.append('sufficient H2 section hierarchy')
    if not architecture['hr_between_sections']: arch_fail.append('HR separation between consecutive H2 sections')
    if not architecture['tables_or_cards']: arch_fail.append('decision-friendly tables/cards')
    if architecture['internal_links'] < 2: arch_fail.append('useful internal links')
    design_fail=[k for k,v in design.items() if not v]
    score=max(0,100-len(missing)*5-len(arch_fail)*4-len(design_fail)*4)
    return {'kind':kind,'score':score,'missing_content':missing,'architecture_failures':arch_fail,'design_failures':design_fail,'h2s':h2s,'architecture':architecture,'design':design}

def gemini_json(prompt,max_output_tokens=12000):
    key=os.getenv('GEMINI_API_KEY')
    if not key: raise RuntimeError('GEMINI_API_KEY is required for benchmark repair')
    endpoint=f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'
    payload={'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json','temperature':0.15,'maxOutputTokens':max_output_tokens}}
    body=json.dumps(payload).encode()
    last=''
    for attempt in range(3):
        try:
            req=Request(endpoint,data=body,method='POST',headers={'Content-Type':'application/json','x-goog-api-key':key,'User-Agent':'MBA-Admission-Portal-Benchmark-Gate/1.0'})
            with urlopen(req,timeout=90) as r: return json.loads(r.read().decode())['candidates'][0]['content']['parts'][0]['text']
        except HTTPError as e:
            last=f'HTTP {e.code}: {e.read().decode(errors="ignore")[:1000]}'
            if e.code in (429,500,502,503,504) and attempt<2: time.sleep(6*(attempt+1)); continue
            raise RuntimeError(last)
        except (URLError,TimeoutError,KeyError,IndexError,ValueError) as e:
            last=str(e)
            if attempt<2: time.sleep(4*(attempt+1)); continue
            raise RuntimeError(last)
    raise RuntimeError(last)

def parse_json(raw):
    raw=re.sub(r'^```(?:json)?','',raw.strip()).strip(); raw=re.sub(r'```$','',raw).strip()
    m=re.search(r'\{.*\}',raw,re.S)
    if not m: raise ValueError('No JSON object returned')
    return json.loads(m.group(0))

def main():
    targets=[x.strip() for x in os.getenv('TARGET_PAGES','').splitlines() if x.strip()]
    if not targets: raise SystemExit('TARGET_PAGES is required for benchmark gate')
    state=load_state(); report=[]
    for name in targets:
        path=(ROOT/name).resolve()
        if path.parent!=ROOT or not path.exists() or path.suffix!='.html': continue
        rank,rec=college_for_page(name,state)
        if not rec: print('No state record for',name); continue
        kind=page_kind(name,rec); before=audit_file(path,kind); best=before
        # A page is allowed to pass only when content, architecture and design gates pass.
        for attempt in range(2):
            if not (best['missing_content'] or best['architecture_failures'] or best['design_failures']): break
            research=rec.get('research_pack',{})
            prompt=f'''You are the final quality editor for an Indian MBA admissions portal.
College: {name} (rank record {rank})
Page kind: {kind}

This page MUST match the locked six-reference production standard:
1) Content depth benchmark: IIM Ahmedabad — complete college-level decision support, exact eligibility/admission/selection logic where officially available, fees, programmes, placements, student/batch context, scholarships, fit and FAQs.
2) Architecture/design benchmark: SIBM Pune — compact text-first hero, Quick Answer, On This Page, short keyword-focused H2s, useful tables/cards, mobile-first hierarchy, clean section separation and internal navigation.
3) Shared requirements across the reference set — student intent first, no generic filler, source discipline, programme-specific facts, current-year caveats, clear interpretation of numbers, and explicit "official information unavailable" when a fact is not supported.

CURRENT AUDIT GAPS:
{json.dumps(best,ensure_ascii=False,indent=2)}

SOURCE RULE: Use ONLY the official-domain research material below. Never invent, estimate or fill a missing number/date/cutoff/fee/intake/weight. Preserve verified claims already on the page unless they conflict with the supplied official material. If a requested module is unsupported, keep the module but state that official information is unavailable rather than hallucinating.

Do not create PhD, certificate, quota-only or unrelated pages.

CURRENT HTML:
{path.read_text(encoding='utf-8')}

OFFICIAL RESEARCH PACK:
{research.get('source_material','')}

Return JSON only: {{"html":"FULL REPAIRED HTML DOCUMENT"}}. Keep the existing college-page.css design system. Do not use markdown fences.'''
            repaired=parse_json(gemini_json(prompt,12000)).get('html','')
            if not repaired: raise RuntimeError('Benchmark repair returned empty HTML')
            path.write_text(repaired,encoding='utf-8')
            best=audit_file(path,kind)
        passed=not(best['missing_content'] or best['architecture_failures'] or best['design_failures'])
        report.append({'page':name,'college_rank':rank,'kind':kind,'passed':passed,'before':before,'after':best})
        if not passed:
            raise SystemExit(f'BENCHMARK GATE FAILED: {name}: {best}')
        print('BENCHMARK PASS',name,kind,best['score'])
    REPORT.write_text(json.dumps({'standard':'six-reference benchmark gate','pages':report},ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__': main()
