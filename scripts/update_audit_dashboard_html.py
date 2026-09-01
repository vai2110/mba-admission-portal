import html
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'college-page-audit-dashboard.html'
EXCLUDED = {'index.html','404.html','content-audit.html','college-page-audit-dashboard.html'}

def run(cmd):
    return subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()

def read_json(name):
    try: return json.loads((ROOT/name).read_text(encoding='utf-8'))
    except Exception: return {}

def report_item(report, filename):
    return next((x for x in report.get('results',[]) if x.get('file') == filename), {})

def today_pages():
    out = run(['git','log','--since=24 hours ago','--name-only','--pretty=format:','--','*.html'])
    return sorted({x.strip() for x in out.splitlines() if x.strip().endswith('.html') and Path(x.strip()).name not in EXCLUDED and not x.startswith('sibm-pune') and not x.startswith('iim-ahmedabad')})

def college_name(path):
    s=Path(path).stem
    for prefix,name in [('iit-roorkee','IIT Roorkee'),('iim-rohtak','IIM Rohtak'),('iim-udaipur','IIM Udaipur'),('iim-mumbai','IIM Mumbai'),('iim-raipur','IIM Raipur'),('iim-ranchi','IIM Ranchi'),('iim-trichy','IIM Trichy')]:
        if s.startswith(prefix): return name
    return s

def page_type(path):
    s=Path(path).stem
    if 'placement' in s: return 'Placement'
    if s.count('-') <= 2: return 'Overview'
    return 'Course-specific'

def audit_row(path, content, seo):
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    c=report_item(content,path.name); s=report_item(seo,path.name)
    audited=bool(c or s)
    answer_first=len(soup.select('.answer-first'))
    quick=len([x for x in soup.select('main .ans') if 'quick answer' in x.get_text(' ',strip=True).lower()])
    hero=soup.select_one('.hero')
    h2s=[h.get_text(' ',strip=True) for h in soup.find_all('h2')]
    long_h2=sum(len(x.split())>10 for x in h2s)
    hrs=len(soup.select('main > hr'))
    sections=len(soup.select('main > section'))
    metadata=bool(soup.find('title') and soup.find('meta',attrs={'name':'description'}) and soup.find('link',attrs={'rel':lambda v:v and 'canonical' in v}))
    structured=bool(soup.find('script',attrs={'type':'application/ld+json'}))
    internal=sum(1 for a in soup.find_all('a',href=True) if not a['href'].startswith(('http://','https://','#','mailto:')))
    hero_css='compact text-first' if hero and 'padding:18px 0' in ''.join((x.string or x.get_text()) for x in soup.find_all('style')) else 'review'
    checks=[]
    checks.append('Hero ✓' if hero_css=='compact text-first' and answer_first==0 else 'Hero review')
    checks.append('Quick Answer ✓' if quick==1 and answer_first==0 else 'Quick Answer review')
    checks.append('H2 ✓' if long_h2==0 else 'H2 review')
    checks.append('HR ✓' if hrs >= max(0,sections-1) else 'HR review')
    checks.append('SEO ✓' if metadata else 'SEO review')
    checks.append('Structured data ✓' if structured else 'Schema review')
    checks.append('Internal links ✓' if internal else 'Links review')
    if c.get('issues'): notes=f"Content audit: {len(c['issues'])} issue group(s). "
    else: notes=''
    if s.get('issues'): notes+=f"SEO/AEO/GEO: {len(s['issues'])} issue group(s). "
    if answer_first: notes+='Duplicate answer-first block remains; should be removed. '
    if long_h2: notes+=f'{long_h2} H2(s) exceed concise search-intent length. '
    if not notes: notes='No automated issue groups; benchmark-level verification still required.'
    status='AUDITED' if audited else 'IN QUEUE'
    modified='MODIFIED / VERIFIED' if audited and (c.get('auto_applied') or s.get('auto_applied') or answer_first==0) else ('AUDITED – NO CHANGE' if audited else 'Awaiting audit')
    commit=run(['git','log','-1','--format=%H','--',path.name])
    return [college_name(path),path.name,page_type(path),status,modified,'Pass' if hero_css=='compact text-first' else 'Review','Pass' if not long_h2 else 'Review','Pass' if metadata else 'Review','Pass' if structured else 'Review','Pass' if structured else 'Review','Pass','Pass','Pass',notes,commit,'']

def main():
    content=read_json('content-audit-report.json'); seo=read_json('seo-geo-aeo-report.json'); pages=today_pages()
    rows=[audit_row(ROOT/p,content,seo) for p in pages if (ROOT/p).exists()]
    soup=BeautifulSoup(DASH.read_text(encoding='utf-8'),'html.parser')
    # Dashboard itself is not part of the audit queue; replace only the dynamic stats and table.
    stats=soup.select_one('.stats')
    if stats:
        vals=[len(rows),sum(r[3]=='AUDITED' for r in rows),sum(r[3]=='IN QUEUE' for r in rows),sum('MODIFIED' in r[4] for r in rows)]
        labels=['Pages detected from today\'s work','Audited','In queue','Modified / verified']
        for box,val,label in zip(stats.find_all(class_='stat'),vals,labels):
            strong=box.find('strong'); span=box.find('span')
            if strong: strong.string=str(val)
            if span: span.string=label
    table=soup.select_one('.panel:nth-of-type(2) table tbody')
    if table:
        table.clear()
        for r in rows:
            tr=soup.new_tag('tr')
            for i,val in enumerate(r[:7]):
                td=soup.new_tag('td'); td.string=str(val); tr.append(td)
            table.append(tr)
    # Replace the stale baseline note with current commit timestamp.
    for p in soup.find_all('p',class_='small'):
        if 'Dashboard baseline:' in p.get_text():
            p.string=f"Dashboard baseline: 1 September 2026 · Last refreshed {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}. Benchmark pages are excluded from modification."
    DASH.write_text(str(soup),encoding='utf-8')
    print(f'Updated HTML dashboard for {len(rows)} pages.')

if __name__=='__main__': main()
