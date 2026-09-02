# MANDATORY SIX-REFERENCE PRODUCTION GATE v2
# This gate enforces IIM Ahmedabad content depth + SIBM Pune architecture/design,
# plus mandatory fees, detailed admission, cutoff tables and latest + prior-three-year placement comparison.
# The full implementation is intentionally kept compact and deterministic.
import csv, json, os, re, time, subprocess, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]; STATE=ROOT/'data/college-production-state.json'; QUEUE=ROOT/'data/college-queue.csv'; REPORT=ROOT/'reference-benchmark-audit.json'; MODEL=os.getenv('GEMINI_MODEL','gemini-3.1-flash-lite')
COMMON=[('identity',['overview','about','history','established']),('admission',['admission','application','apply','selection','shortlist']),('eligibility',['eligibility','eligible','qualification']),('exam',['cat','xat','gmat','nmat','snap','entrance','exam']),('cutoff',['cutoff','cut-off','percentile','screening','not officially published','student reported']),('fees',['fee','fees','tuition','total cost','fee structure','fee breakup','fee bifurcation']),('programmes',['programme','program','course']),('placements',['placement','placements','salary','ctc','recruiter']),('faqs',['faq','frequently asked']),('official_sources',['official sources','official website','source'])]
OVERVIEW=COMMON+[('rankings',['ranking','nirf']),('selection_logic',['selection criteria','selection process','weight','composite']),('dates',['important dates','deadline','schedule','last date']),('student_profile',['batch profile','student profile','class profile','work experience']),('student_life',['student life','campus life','clubs','community','campus']),('scholarships',['scholarship','financial aid','fee waiver']),('fit',['who should','who can apply','fit','suitable','consider']),('placement_three_year',['2025','2024','2023','year-wise','year wise','comparison']),('fee_table',['fee structure','fee breakup','fee bifurcation','total fee','course fee','academic fee']),('admission_detail',['step 1','step 2','step 3','admission process','application process'])]
PLACEMENT=[('placement_overview',['placement','career outcomes']),('latest_metrics',['average','median','highest','ctc','lpa']),('yearwise_trend',['2025','2024','2023','trend','year-wise','year wise','comparison']),('three_year_table',['2025','2024','2023','2025-26','2024-25','2023-24']),('recruiters',['recruiter','companies','organizations']),('sectors',['sector','industry']),('roles',['role','roles','function','profile']),('summer',['summer internship','internship','stipend']),('how_to_read',['how to read','interpret','should students']),('official_sources',['official sources','placement report','official website']),('faqs',['faq','frequently asked'])]
COURSE=COMMON+[('course_overview',['programme overview','program overview','duration','full-time','weekend']),('selection_logic',['selection criteria','selection process','shortlist','weight']),('curriculum',['curriculum','course structure','trimesters','semester','subjects']),('specialisations',['specialisation','specialization','major','elective']),('career_outcomes',['career','roles','recruiters','placements']),('fit',['who should','fit','suitable','freshers','work experience']),('fee_table',['fee structure','fee breakup','fee bifurcation','total fee','course fee','academic fee']),('admission_detail',['step 1','step 2','step 3','admission process','application process']),('cutoff_table',['cutoff table','cut-off table','percentile table','screening cutoff','student reported'])]

def state(): return json.loads(STATE.read_text(encoding='utf-8'))
def college_for(name,s):
  with QUEUE.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
  for rank,rec in s.get('colleges',{}).items():
    if name in rec.get('course_filenames',[]): return int(rank),rec
    row=next((r for r in rows if str(r['rank'])==str(rank)),None)
    if row:
      b=re.sub(r'[^a-z0-9]+','-',(rec.get('popular_name') or row['college_name']).lower()).strip('-')
      if name in (b+'.html',b+'-placements.html'): return int(rank),rec
  return None,None
def kind(name,rec): return 'placement' if name.endswith('-placements.html') else ('course' if name in rec.get('course_filenames',[]) else 'overview')
def text(s):
  x=BeautifulSoup(str(s),'html.parser')
  for t in x(['script','style','noscript','svg','nav','header','footer']): t.decompose()
  return re.sub(r'\s+',' ',x.get_text(' ',strip=True)).lower()
def audit(path,k):
  s=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser'); t=text(s); req=OVERVIEW if k=='overview' else PLACEMENT if k=='placement' else COURSE
  missing=[n for n,terms in req if not any(z in t for z in terms)]; tables=s.find_all('table')
  fee_table=any(any(z in q.get_text(' ',strip=True).lower() for z in ('fee','tuition','cost')) for q in tables)
  placement_table=any((('2025' in q.get_text() and '2024' in q.get_text() and '2023' in q.get_text()) or ('2025-26' in q.get_text() and '2024-25' in q.get_text() and '2023-24' in q.get_text())) for q in tables)
  cutoff_table=any(any(z in q.get_text(' ',strip=True).lower() for z in ('cutoff','percentile','screening')) for q in tables)
  arch={'quick_answer':bool(s.select_one('.answer,.quick-answer,[class*="answer"]')),'on_this_page':'on this page' in t or bool(s.select_one('nav a[href^="#"]')),'h2_count':len(s.find_all('h2')),'tables_or_cards':bool(tables or s.select_one('.card,.cards,.grid,.fact,.facts')),'internal_links':sum(1 for a in s.find_all('a',href=True) if not a['href'].startswith(('http://','https://','#','mailto:'))),'has_fee_table':fee_table,'has_placement_comparison_table':placement_table,'has_cutoff_table':cutoff_table}
  main=s.find('main'); hr=True
  if main:
    secs=main.find_all('section',recursive=False)
    for sec in secs[1:]:
      p=sec.previous_sibling
      while p is not None and getattr(p,'name',None) is None and not str(p).strip(): p=p.previous_sibling
      if getattr(p,'name',None)!='hr': hr=False; break
  arch['hr_between_sections']=hr; fails=[]
  if not arch['quick_answer']: fails.append('Quick Answer')
  if not arch['on_this_page']: fails.append('On This Page')
  if arch['h2_count']<(8 if k=='overview' else 7 if k=='course' else 6): fails.append('section hierarchy')
  if not hr: fails.append('HR separation')
  if not arch['tables_or_cards']: fails.append('tables/cards')
  if arch['internal_links']<2: fails.append('internal links')
  if k in ('overview','course') and not fee_table: fails.append('mandatory latest official fee table/bifurcation')
  if k in ('overview','course') and not cutoff_table: fails.append('mandatory cutoff table or explicit unavailable/student-reported table')
  if k in ('overview','placement') and not placement_table: fails.append('mandatory latest + prior three-year placement comparison table')
  design={'viewport':bool(s.find('meta',attrs={'name':'viewport'})),'shared_css':bool(any('college-page.css' in (l.get('href') or '') for l in s.find_all('link',href=True))),'hero':bool(s.select_one('.hero')),'responsive':bool(s.find('link',href=lambda x:x and 'college-page.css' in x)),'single_h1':len(s.find_all('h1'))==1}; df=[x for x,v in design.items() if not v]
  return {'kind':k,'score':max(0,100-len(missing)*5-len(fails)*4-len(df)*4),'missing_content':missing,'architecture_failures':fails,'design_failures':df,'architecture':arch,'design':design}
def gemini(prompt):
  key=os.getenv('GEMINI_API_KEY'); endpoint=f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'; payload={'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'responseMimeType':'application/json','temperature':0.1,'maxOutputTokens':12000}}; body=json.dumps(payload).encode()
  for a in range(4):
    try:
      req=Request(endpoint,data=body,method='POST',headers={'Content-Type':'application/json','x-goog-api-key':key});
      with urlopen(req,timeout=90) as r: return json.loads(r.read().decode())['candidates'][0]['content']['parts'][0]['text']
    except (HTTPError,URLError,TimeoutError,KeyError,IndexError,ValueError):
      if a==3: raise
      time.sleep(5*(a+1))
def parse(x):
  x=re.sub(r'^```(?:json)?','',x.strip()).strip(); x=re.sub(r'```$','',x).strip(); m=re.search(r'\{.*\}',x,re.S)
  if not m: raise ValueError('No JSON returned')
  return json.loads(m.group(0))
def main():
  targets=[x.strip() for x in os.getenv('TARGET_PAGES','').splitlines() if x.strip()]; s=state(); report=[]
  if not targets: raise SystemExit('TARGET_PAGES required')
  for name in targets:
    p=(ROOT/name).resolve();
    if p.parent!=ROOT or not p.exists(): continue
    rank,rec=college_for(name,s)
    if not rec: continue
    k=kind(name,rec); before=audit(p,k); best=before
    for _ in range(4):
      if not(best['missing_content'] or best['architecture_failures'] or best['design_failures']): break
      rp=rec.get('research_pack',{}); prompt=f'''Repair ONLY the deficiencies identified in this audit while preserving all valid existing content. The output MUST satisfy every audit item; do not merely describe changes. Use IIM Ahmedabad as content-depth benchmark and SIBM Pune as architecture/design benchmark. Never invent facts. Use only supplied official research; if an official fact is absent, explicitly state that it is unavailable. For cutoff, create a real HTML table with an explicitly labelled official-unavailable/student-reported status rather than prose. For placement comparison, create a real HTML table containing the latest year and the previous three years; use exact official figures when present in the supplied research and write "Official data not available in supplied research material" only where a year is genuinely unavailable. Preserve/add <link rel="stylesheet" href="college-page.css">, a .hero, a Quick Answer block, On This Page navigation, at least the required number of H2 sections, at least two relative internal links to existing portal pages, and <hr> between top-level sections. Admission process must be sequential and factual from supplied research. Do not remove existing useful tables or facts.
AUDIT TO FIX: {json.dumps(best,ensure_ascii=False)}
CURRENT HTML:\n{p.read_text(encoding='utf-8')}
OFFICIAL RESEARCH:\n{rp.get('source_material','')}
STUDENT DISCUSSION CUTOFF MATERIAL (UNOFFICIAL ONLY):\n{rp.get('student_discussion_material','')}
Return JSON only with key html containing the FULL repaired HTML document. Do not return commentary.'''
      repaired=parse(gemini(prompt)).get('html','')
      if not repaired: raise RuntimeError('Empty repaired HTML')
      p.write_text(repaired,encoding='utf-8'); best=audit(p,k)
    if best['missing_content'] or best['architecture_failures'] or best['design_failures']:
      print(f'Gemini repair incomplete for {name}; invoking deterministic structural recovery.')
      env=os.environ.copy(); env['TARGET_PAGES']=name
      subprocess.run([sys.executable,str(ROOT/'scripts/deterministic_benchmark_repair.py')],env=env,cwd=ROOT,check=True)
      best=audit(p,k)
    passed=not(best['missing_content'] or best['architecture_failures'] or best['design_failures']); report.append({'page':name,'college_rank':rank,'kind':k,'passed':passed,'before':before,'after':best})
    if not passed: raise SystemExit(f'BENCHMARK GATE FAILED: {name}: {best}')
    print('BENCHMARK PASS',name,k,best['score'])
  REPORT.write_text(json.dumps({'standard':'six-reference benchmark + mandatory fees/admission/cutoff/latest + prior-three-year placements','pages':report},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
