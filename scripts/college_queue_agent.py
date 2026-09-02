import csv, json, os, re, subprocess, time
from pathlib import Path
from bs4 import BeautifulSoup
from openai import OpenAI

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/'data/college-queue.csv'; STATE=ROOT/'data/college-production-state.json'
MODEL=os.getenv('OPENAI_MODEL','gpt-5.6-luna'); DONE='Created + Audited'
COLS=['Overview Page','Placement Page','Course Page 1','Course Page 2','Course Page 3']

def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower().replace('&',' and ')).strip('-')
def loadq():
    with QUEUE.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def loads(): return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'legacy_completed_ranks':list(range(1,22)),'colleges':{}}
def saves(s): STATE.write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def pending(q,s):
    legacy={int(x) for x in s.get('legacy_completed_ranks',[])}
    for row in q:
        rank=int(row['rank'])
        if rank in legacy: continue
        rec=s.setdefault('colleges',{}).setdefault(str(rank),{})
        if any(rec.get(c) not in (DONE,'Not Applicable') for c in COLS): return row
    return None

def ask(client,prompt,domain):
    """Use official-domain web search first, then retry without domain filtering if the
    hosted search configuration is rejected. The prompt still explicitly requires
    official-domain-only research, so the fallback is used only for API robustness."""
    primary={
        'type':'web_search',
        'filters':{'allowed_domains':[domain]},
        'search_context_size':'high'
    }
    last_error=None
    for attempt in range(2):
        try:
            r=client.responses.create(model=MODEL,tools=[primary],input=prompt)
            return r.output_text
        except Exception as exc:
            last_error=exc
            if attempt == 0:
                time.sleep(2)
    # Some API/project configurations can reject domain-filtered hosted search even
    # though web_search itself is available. Retry with unrestricted web search and
    # enforce the official-domain restriction in the research prompt.
    try:
        r=client.responses.create(
            model=MODEL,
            tools=[{'type':'web_search','search_context_size':'high'}],
            input=prompt + f"\n\nFALLBACK SEARCH RULE: Use only the official domain {domain} and its subdomains. Do not use third-party sources."
        )
        return r.output_text
    except Exception as exc:
        raise RuntimeError(f'OpenAI web research failed after domain-filtered and fallback attempts. Primary error: {last_error}; fallback error: {exc}') from exc

def json_out(text):
    text=text.strip(); text=re.sub(r'^```(?:json)?','',text).strip(); text=re.sub(r'```$','',text).strip()
    m=re.search(r'\{.*\}',text,re.S)
    if not m: raise ValueError('Model did not return JSON')
    return json.loads(m.group(0))
def validate(html):
    soup=BeautifulSoup(html,'html.parser')
    if not soup.find('html') or not soup.find('title') or not soup.find('h1'): raise ValueError('Missing html/title/h1')
    if not soup.find('meta',attrs={'name':'description'}): raise ValueError('Missing meta description')
    if not soup.find('link',attrs={'rel':'canonical'}): raise ValueError('Missing canonical')
    if html.lower().count('<html')!=1: raise ValueError('Invalid HTML structure')
def commit(msg):
    subprocess.run(['git','config','user.name','MBA Portal College Agent'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','add','*.html','data/college-production-state.json'],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode: return
    subprocess.run(['git','commit','-m',msg],cwd=ROOT,check=True); subprocess.run(['git','push'],cwd=ROOT,check=True)

def main():
    if not os.getenv('OPENAI_API_KEY'): raise SystemExit('OPENAI_API_KEY GitHub secret is required for autonomous creation.')
    q=loadq(); s=loads(); client=OpenAI(); row=pending(q,s)
    if not row: print('QUEUE COMPLETE'); return
    rank=int(row['rank']); college=row['college_name']; domain=row['official_url'].replace('https://','').replace('http://','').split('/')[0]
    rec=s.setdefault('colleges',{}).setdefault(str(rank),{}); print(f'Next college: #{rank} {college}')
    if 'course_plan' not in rec:
        p=f'''Research ONLY the official website of {college} at {domain}. Identify up to three distinct, substantial MBA/management programmes that deserve dedicated student pages. Do not invent programmes. Exclude PhD/doctoral programmes, certificates, short courses, and quota/category-only pages. Do not create thin pages. If the college has fewer than three substantial MBA/management programmes, return only those actually offered. For IIT Roorkee specifically, the dedicated course pages should be MBA and Executive MBA, excluding PhD. Return JSON only: {{"courses":[{{"name":"..."}},{{"name":"..."}},{{"name":"..."}}]}}.'''
        plan=json_out(ask(client,p,domain)); courses=[x for x in plan.get('courses',[]) if x and x.get('name')][:3]
        rec['course_plan']=courses; rec['course_filenames']=[f"{slug(college)}-{slug(x['name'])}.html" if x else None for x in courses]
        while len(rec['course_plan'])<3: rec['course_plan'].append(None); rec['course_filenames'].append(None)
        saves(s)
    targets=[('Overview Page',f'{slug(college)}.html','overview'),('Placement Page',f'{slug(college)}-placements.html','placement')]
    for i,c in enumerate(rec['course_plan']):
        key=f'Course Page {i+1}'
        if c: targets.append((key,rec['course_filenames'][i],'course'))
        else: rec[key]='Not Applicable'
    saves(s)
    created_pages=[]
    for col,filename,kind in targets:
        if rec.get(col)==DONE: continue
        rec[col]='Creating'; saves(s)
        focus='college overview and admission' if kind=='overview' else 'placements' if kind=='placement' else 'dedicated programme '+next(c['name'] for i,c in enumerate(rec['course_plan']) if c and rec['course_filenames'][i]==filename)
        prompt=f'''Create one production-ready HTML document for an Indian MBA admissions portal about {college}. Official website: https://{domain}. Focus: {focus}. It will publish directly to GitHub Pages.

Locked standards: IIM Ahmedabad is the content-depth benchmark (exact eligibility, selection logic, programme facts, student intent, official-source discipline). SIBM Pune is the architecture/design benchmark (compact text-first hero, clean navigation, hierarchy, useful tables/cards, mobile-first). Link college-page.css. Use simple student-centric English; no generic filler. Research ONLY official sources on the supplied domain. Never invent fees, cutoffs, dates, intake, placement numbers, selection weights or programmes; say when official data is unavailable. Do not create quota/category-only or PhD pages. Include unique title, meta description, canonical, OG/Twitter, one H1, JSON-LD where appropriate, one Quick Answer, On This Page navigation, FAQs, official source links, internal links when known, keyword-focused short H2s, and <hr> between consecutive H2 sections. Placement pages must use latest official data and up to three comparable years where available. Overview pages cover admission, eligibility, application, entrance, shortlist, selection, fees, programmes and placements where available. Course pages cover overview, duration, eligibility, admission, curriculum/specialisations, fees, selection, outcomes and FAQs. Return JSON only as {{"html":"FULL HTML DOCUMENT"}} with no markdown fences.'''
        try:
            html=json_out(ask(client,prompt,domain))['html']; validate(html); (ROOT/filename).write_text(html,encoding='utf-8'); rec[col]='Created — Audit Pending'; created_pages.append(filename); saves(s); print('CREATED',filename)
        except Exception as e:
            rec[col]='Needs Review'; rec.setdefault('errors',[]).append({'page':col,'error':str(e)}); saves(s); raise
    if created_pages:
        rec['created_pages_last_run']=created_pages
        saves(s)
        commit(f'Create {college} college page cluster')

if __name__=='__main__': main()
