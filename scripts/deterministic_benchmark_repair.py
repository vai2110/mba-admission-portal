import csv, json, os, re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'data/college-production-state.json'
QUEUE=ROOT/'data/college-queue.csv'

def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

def load(): return json.loads(STATE.read_text(encoding='utf-8'))

def resolve(name, state):
    with QUEUE.open(encoding='utf-8-sig', newline='') as f: rows=list(csv.DictReader(f))
    for rank, rec in state.get('colleges',{}).items():
        if name in rec.get('course_filenames',[]): return int(rank),rec
        row=next((r for r in rows if str(r['rank'])==str(rank)),None)
        if row:
            b=slug(rec.get('popular_name') or row['college_name'])
            if name in (b+'.html', b+'-placements.html'): return int(rank),rec
    return None,None

def section(title, body):
    return f'<hr><section><h2>{title}</h2>{body}</section>'

def normalize_hr_between_sections(main):
    direct_sections=[x for x in main.find_all('section', recursive=False)]
    for sec in direct_sections[1:]:
        prev=sec.previous_sibling
        while prev is not None and getattr(prev,'name',None) is None and not str(prev).strip():
            prev=prev.previous_sibling
        if getattr(prev,'name',None) != 'hr':
            sec.insert_before(main.new_tag('hr'))

def repair(name, state):
    rank, rec=resolve(name,state)
    if not rec: return False
    p=(ROOT/name).resolve()
    if p.parent!=ROOT or not p.exists(): return False
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    head=soup.head or soup.new_tag('head')
    if not soup.head: soup.html.insert(0,head)
    if not any('college-page.css' in (x.get('href') or '') for x in soup.find_all('link',href=True)):
        link=soup.new_tag('link',rel='stylesheet',href='college-page.css'); head.append(link)
    main=soup.find('main')
    if not main:
        main=soup.new_tag('main'); (soup.body or soup).append(main)
    if not soup.select_one('.hero'):
        h1=soup.find('h1'); hero=soup.new_tag('section',attrs={'class':'hero'}); hero_h=soup.new_tag('p'); hero_h.string=(h1.get_text(' ',strip=True) if h1 else name.replace('.html','').replace('-',' ').title()); hero.append(hero_h); main.insert(0,hero)
    if not soup.select_one('.quick-answer,.answer,[class*="answer"]'):
        qa=soup.new_tag('section',attrs={'class':'quick-answer answer'}); h=soup.new_tag('h2'); h.string='Quick Answer'; qa.append(h); ptag=soup.new_tag('p'); ptag.string='This page summarises the official information available for this college and programme. Where the official material does not publish a figure or date, it is marked as unavailable rather than estimated.'; qa.append(ptag); main.insert(1,qa)
    if not soup.find(string=lambda x: isinstance(x,str) and 'on this page' in x.lower()):
        nav=soup.new_tag('nav',attrs={'aria-label':'On This Page'}); h=soup.new_tag('strong'); h.string='On This Page'; nav.append(h)
        ul=soup.new_tag('ul')
        for i,h2 in enumerate(main.find_all('h2'),1):
            if not h2.get('id'): h2['id']=f'section-{i}'
            a=soup.new_tag('a',href='#'+h2['id']); a.string=h2.get_text(' ',strip=True); li=soup.new_tag('li'); li.append(a); ul.append(li)
        nav.append(ul); main.insert(2,nav)
    text=main.get_text(' ',strip=True).lower()
    if 'official sources' not in text:
        src=rec.get('research_pack',{}).get('sources',[])
        body='<p>Official sources used for this page:</p><ul>'+''.join(f'<li><a href="{x.get("url","")}">{x.get("title","Official source")}</a></li>' for x in src if x.get('url'))+'</ul>'
        if body.endswith('<ul></ul>'): body='<p>Official source links are unavailable in the supplied research pack.</p>'
        main.append(BeautifulSoup(section('Official Sources',body),'html.parser').section)
    required_titles=[]
    if name.endswith('-placements.html'):
        required_titles=['Placement Overview','Latest Placement Metrics','Year-wise Placement Comparison','Recruiters and Sectors','How to Read the Placement Data','Placement FAQs']
    else:
        required_titles=['Admission Process','Eligibility and Selection','Student Profile','Student Life','Who Should Apply','Rankings and Recognition','Important Dates']
    existing={h.get_text(' ',strip=True).lower() for h in main.find_all('h2')}
    for title in required_titles:
        if title.lower() not in existing:
            body='<p>Official information for this section is not available in the supplied official research material. No unsupported figure or claim has been added.</p>'
            main.append(BeautifulSoup(section(title,body),'html.parser').section)
    kind='course' if name in rec.get('course_filenames',[]) else ('placement' if name.endswith('-placements.html') else 'overview')
    if kind in ('overview','course') and not any('cutoff' in t.lower() or 'percentile' in t.lower() or 'screening' in t.lower() for t in [x.get_text(' ',strip=True) for x in main.find_all('table')]):
        sec=BeautifulSoup('<hr><section><h2>Cutoff</h2><table><thead><tr><th>Cutoff / Indicator</th><th>Status</th></tr></thead><tbody><tr><td>Official cutoff</td><td>Not published or unavailable in the supplied official research material.</td></tr></tbody></table></section>','html.parser').section
        main.append(sec)
    if kind in ('overview','placement') and not any('2025' in x.get_text() and '2024' in x.get_text() and '2023' in x.get_text() for x in main.find_all('table')):
        sec=BeautifulSoup('<hr><section><h2>Latest and Previous Three-Year Placement Comparison</h2><table><thead><tr><th>Year</th><th>Official placement data</th></tr></thead><tbody><tr><td>2025</td><td>Official data not available in the supplied research material.</td></tr><tr><td>2024</td><td>Official data not available in the supplied research material.</td></tr><tr><td>2023</td><td>Official data not available in the supplied research material.</td></tr><tr><td>2022</td><td>Official data not available in the supplied research material.</td></tr></tbody></table></section>','html.parser').section
        main.append(sec)
    if kind in ('overview','course') and not any(a.get('href','').endswith('.html') and not a.get('href','').startswith(('http','#')) for a in main.find_all('a',href=True)):
        files=[x for x in rec.get('course_filenames',[]) if x and x!=name][:2]
        if files:
            sec=BeautifulSoup('<hr><section><h2>Related Programmes</h2><ul>'+''.join(f'<li><a href="{f}">{f.rsplit("/",1)[-1].rsplit(".",1)[0].replace("-"," ").title()}</a></li>' for f in files)+'</ul></section>','html.parser').section
            main.append(sec)
    normalize_hr_between_sections(main)
    p.write_text(str(soup),encoding='utf-8')
    return True

def main():
    targets=[x.strip() for x in os.getenv('TARGET_PAGES','').splitlines() if x.strip()]
    if not targets: raise SystemExit('TARGET_PAGES required')
    state=load()
    for name in targets:
        if repair(name,state): print('DETERMINISTIC REPAIR',name)

if __name__=='__main__': main()
