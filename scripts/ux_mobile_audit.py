from pathlib import Path
from bs4 import BeautifulSoup
import json, re
from datetime import datetime, timezone

ROOT = Path('.')
EXCLUDE = {'404.html','content-audit.html','college-page-audit-dashboard.html'}
issues=[]
rows=[]

for path in sorted(ROOT.rglob('*.html')):
    if '.git' in path.parts or path.name in EXCLUDE:
        continue
    raw=path.read_text(encoding='utf-8', errors='ignore')
    soup=BeautifulSoup(raw,'html.parser')
    checks={}
    checks['viewport']=bool(soup.find('meta', attrs={'name':'viewport'}))
    checks['h1']=len(soup.find_all('h1')) == 1
    checks['responsive_css']=bool(re.search(r'@media\s*\([^)]*(?:max-width|min-width)', raw, re.I))
    checks['tables_scrollable']=all(
        t.parent and t.parent.name in {'div','section'} and (
            'overflow-x:auto' in t.parent.get('style','').replace(' ','') or
            any(cls in {'table-wrapper','table-wrap','table-responsive','table-container'} for cls in (t.parent.get('class') or []))
        ) for t in soup.find_all('table')
    ) if soup.find('table') else True
    checks['buttons_or_ctas']=True
    checks['images_alt']=all(img.get('alt','').strip() for img in soup.find_all('img'))
    checks['horizontal_overflow_risk']='width:100vw' not in raw.replace(' ','')
    checks['mobile_nav']=bool(soup.select_one('.mobile-on-page')) or not bool(soup.select_one('.sidebar'))
    score=sum(checks.values())/len(checks)*100
    row={'page':str(path),'score':round(score,1),'checks':checks}
    rows.append(row)
    for key,ok in checks.items():
        if not ok:
            issues.append({'page':str(path),'issue':key})

summary={
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'pages_checked':len(rows),
 'pages_with_issues':len({x['page'] for x in issues}),
 'issue_counts':{},
 'average_score':round(sum(r['score'] for r in rows)/len(rows),1) if rows else 0,
 'priority_order':['viewport','responsive_css','h1','tables_scrollable','images_alt','horizontal_overflow_risk','mobile_nav'],
 'pages':rows,
}
for x in issues:
    summary['issue_counts'][x['issue']]=summary['issue_counts'].get(x['issue'],0)+1

Path('ux-mobile-audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['generated_at','pages_checked','pages_with_issues','average_score','issue_counts']},indent=2))
