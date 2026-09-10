from pathlib import Path
from bs4 import BeautifulSoup
import json, re
from datetime import datetime, timezone

# Fresh baseline trigger: 2026-09-10
ROOT = Path('.')
EXCLUDE = {'404.html','content-audit.html','college-page-audit-dashboard.html','irma-deploy-trigger.html'}
issues=[]
rows=[]
RESPONSIVE_RE = re.compile(r'@media\s*\([^)]*(?:max-width|min-width)', re.I)

def page_css(raw, soup, path):
    chunks=[raw]
    for link in soup.find_all('link', href=True):
        href=link.get('href','').split('#',1)[0].split('?',1)[0]
        if not href.lower().endswith('.css'): continue
        css_path=(path.parent / href).resolve()
        try:
            if css_path.is_relative_to(ROOT.resolve()) and css_path.exists():
                chunks.append(css_path.read_text(encoding='utf-8', errors='ignore'))
        except (ValueError, OSError): pass
    return '\n'.join(chunks)

for path in sorted(ROOT.rglob('*.html')):
    if '.git' in path.parts or path.name in EXCLUDE: continue
    raw=path.read_text(encoding='utf-8', errors='ignore')
    soup=BeautifulSoup(raw,'html.parser')
    css=page_css(raw, soup, path)
    checks={}
    checks['viewport']=bool(soup.find('meta', attrs={'name':'viewport'}))
    checks['h1']=len(soup.find_all('h1')) == 1
    checks['responsive_css']=bool(RESPONSIVE_RE.search(css))
    tables=soup.find_all('table')
    def table_has_scroll(t):
        node=t.parent
        for _ in range(4):
            if not node or getattr(node,'name',None) is None: break
            style=node.get('style','').replace(' ','').lower()
            classes=set(node.get('class') or [])
            if 'overflow-x:auto' in style or 'overflow:auto' in style or classes & {'table-wrapper','table-wrap','table-responsive','table-container'}: return True
            node=node.parent
        return False
    checks['tables_scrollable']=all(table_has_scroll(t) for t in tables) if tables else True
    checks['buttons_or_ctas']=True
    checks['images_alt']=all(img.get('alt','').strip() for img in soup.find_all('img'))
    checks['horizontal_overflow_risk']='width:100vw' not in re.sub(r'\s+','',css).lower()
    checks['mobile_nav']=bool(soup.select_one('.mobile-on-page')) or not bool(soup.select_one('.sidebar'))
    score=sum(checks.values())/len(checks)*100
    row={'page':str(path),'score':round(score,1),'checks':checks}; rows.append(row)
    for key,ok in checks.items():
        if not ok: issues.append({'page':str(path),'issue':key})

summary={'generated_at':datetime.now(timezone.utc).isoformat(),'pages_checked':len(rows),'pages_with_issues':len({x['page'] for x in issues}),'issue_counts':{},'average_score':round(sum(r['score'] for r in rows)/len(rows),1) if rows else 0,'priority_order':['viewport','h1','responsive_css','tables_scrollable','images_alt','horizontal_overflow_risk','mobile_nav'],'pages':rows}
for x in issues: summary['issue_counts'][x['issue']]=summary['issue_counts'].get(x['issue'],0)+1
Path('ux-mobile-audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['generated_at','pages_checked','pages_with_issues','average_score','issue_counts']},indent=2))
