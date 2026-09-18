#!/usr/bin/env python3
import json, os, re, sys, time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlencode
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL", "").strip()
SHEET_SECRET = os.getenv("GOOGLE_SHEETS_API_SECRET", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
BATCH_SIZE = 1
YEAR = "2026"

GUIDELINE = r"""
Audit and improve the EXISTING college HTML page; never create a new college page.
Google intent: college admission, fees, placements, reviews.
Student intent: eligibility, how to apply, dates, seats/quota, fees/total cost, scholarships,
placements, campus, rankings, reviews and FAQs.
Sections to audit: Admission; Courses & Fees; Rankings & Placements; Campus & Facilities;
SEO & Content Quality; AI Citation Readiness.
Required output quality: answer-first opening, Quick Facts, tentative upcoming admission dates,
detailed bullet admission process, fee bifurcation and estimated total cost, latest and year-wise
placement tables, student-intent accordion FAQs, important points bold, clean internal links,
fresh year labels on dynamic facts, no fabricated facts.
If a fact cannot be verified from supplied official sources, write exactly
[To be updated: source from official website].
Tables must be usable on mobile without horizontal scrolling.
On This Page must remain compact and usable on mobile.
Do not use vague promotional claims. Do not invent reviews or statistics.
Preserve the existing site's visual identity and useful existing content unless a change is required.
"""

def http(url, data=None, headers=None, method="GET", timeout=30):
    last=None
    for attempt in range(6):
        try:
            req = Request(url, data=data, headers=headers or {"User-Agent":"CollegeDecoded-Audit/1.0"}, method=method)
            with urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last=e
            code=getattr(e,"code",None)
            if code not in (429,500,502,503,504):
                raise
            if attempt<5:
                time.sleep(5*(attempt+1))
    raise last
def sheet(action, post=False, **fields):
    if not SHEET_URL:
        raise RuntimeError("GOOGLE_SHEET_WEBAPP_URL missing")
    if post:
        if not SHEET_SECRET:
            raise RuntimeError("GOOGLE_SHEETS_API_SECRET missing")
        body=json.dumps({"secret":SHEET_SECRET,"action":action,**fields}).encode()
        raw=http(SHEET_URL, body, {"Content-Type":"application/json","User-Agent":"CollegeDecoded-Audit/1.0"},"POST")
    else:
        q=urlencode({"action":action,**fields})
        raw=http(SHEET_URL + ("&" if "?" in SHEET_URL else "?") + q)
    out=json.loads(raw)
    if not out.get("success"):
        raise RuntimeError(out.get("error","Google Sheet request failed"))
    return out

def normalize(s):
    return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")

def find_existing_pages(college, homepage):
    slug=normalize(college)
    candidates=[]
    for p in ROOT.glob("*.html"):
        n=p.stem.lower()
        if slug in n or n in slug or any(x in n for x in slug.split("-") if len(x)>3):
            candidates.append(p)
    if not candidates:
        raise RuntimeError(f"No existing HTML page found for {college} (slug {slug})")
    return sorted(candidates, key=lambda p: (0 if p.stem==slug else 1, len(p.name)))

def official_pack(homepage, max_pages=8):
    if not homepage.startswith(("http://","https://")):
        raise RuntimeError("Invalid homepage URL")
    root=http(homepage)
    soup=BeautifulSoup(root,"html.parser")
    domain=urlparse(homepage).netloc.lower().replace("www.","")
    links=[]
    for a in soup.find_all("a",href=True):
        u=urljoin(homepage,a["href"]).split("#")[0]
        if urlparse(u).netloc.lower().replace("www.","")==domain and u not in links:
            links.append(u)
    preferred=[]
    keys=("admission","fee","course","program","placement","scholar","hostel","campus","ranking","contact")
    for u in links:
        if any(k in u.lower() for k in keys):
            preferred.append(u)
    urls=[homepage]+preferred
    for u in links:
        if u not in urls: urls.append(u)
        if len(urls)>=max_pages: break
    pages=[]
    for u in urls[:max_pages]:
        try:
            txt=BeautifulSoup(http(u), "html.parser").get_text(" ", strip=True)
            pages.append({"url":u,"text":txt[:12000]})
        except Exception:
            pass
    return pages

def gemini(prompt):
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GEMINI_KEY}"
    payload={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.15,"responseMimeType":"application/json"}}
    raw=http(url,json.dumps(payload).encode(),{"Content-Type":"application/json"},"POST",90)
    data=json.loads(raw)
    text=data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)

def main():
    if not GEMINI_KEY: raise RuntimeError("GEMINI_API_KEY missing")
    batch=sheet("assignBatch",post=True,batchSize=BATCH_SIZE).get("colleges",[])
    if not batch:
        print("NO_PENDING_COLLEGE")
        return 0
    college=batch[0]
    name=str(college.get("collegeName") or college.get("College Name") or "").strip()
    rank=str(college.get("rank") or "").strip()
    homepage=str(college.get("officialWebsite") or college.get("Official Website Links") or "").strip()
    if not name or not homepage:
        raise RuntimeError("Selected Sheet row lacks college name or homepage URL")
    sheet("updateStatus",post=True,rank=int(rank),researchStatus="Auditing")
    pages=find_existing_pages(name,homepage)
    pack=official_pack(homepage)
    live_urls=[]
    for p in pages:
        live_urls.append("https://vai2110.github.io/mba-admission-portal/"+p.name)
    source_text="\n\n".join(f"SOURCE: {x['url']}\n{x['text']}" for x in pack)
    page_text="\n\n".join(f"FILE: {p.name}\n{p.read_text(encoding='utf-8')}" for p in pages[:4])
    prompt=f"""You are an existing-page SEO and student-intent editor.
College: {name}
Rank: {rank}
Official homepage: {homepage}
Existing live/source pages:
{page_text}
Official-source research:
{source_text}
MASTER GUIDELINE:
{GUIDELINE}
Return JSON only with keys:
files: array of objects {{path, html}}
overall_score: integer 0-100
updates_required: string
section_scores: object
summary: string
Rules:
- Return modified HTML only for files supplied above.
- Do not invent data.
- Keep existing page URL/file identity.
- Verify college identity; if the official homepage clearly belongs to another college, return error=true and do not modify files.
- Every dynamic numeric fact must carry a year/context.
- FAQ must use <details class="accordion"><summary>...</summary><div class="faq-answer">...</div></details>.
- Keep tables responsive without requiring horizontal scrolling.
- Keep On This Page compact on mobile.
- Remove irrelevant/promotional/citation-language text.
- Use [To be updated: source from official website] where official verification is unavailable.
- Preserve useful existing CSS/JS and existing verified content.
- Do not output markdown fences.
"""
    result=gemini(prompt)
    if result.get("error"):
        raise RuntimeError(result.get("message","Audit rejected due to college identity mismatch"))
    returned={x["path"]:x["html"] for x in result.get("files",[]) if x.get("path") and x.get("html")}
    changed=[]
    for p in pages:
        if p.name not in returned: continue
        html=returned[p.name]
        soup=BeautifulSoup(html,"html.parser")
        if soup.find("h1") is None or soup.title is None or name.lower() not in soup.get_text(" ",strip=True).lower():
            raise RuntimeError(f"HTML validation failed for {p.name}")
        if len(soup.find_all("h1")) != 1:
            raise RuntimeError(f"Expected exactly one H1 in {p.name}")
        if soup.find_all("details",class_="accordion"):
            for d in soup.find_all("details",class_="accordion"):
                if not d.find("summary") or not d.find(class_="faq-answer"):
                    raise RuntimeError(f"FAQ accordion validation failed for {p.name}")
        p.write_text(html,encoding="utf-8")
        changed.append(p.name)
    if not changed:
        raise RuntimeError("Audit produced no editable existing HTML")
    Path("changed-html.txt").write_text("\n".join(changed)+"\n",encoding="utf-8")
    Path("college-audit-result.json").write_text(json.dumps({"college":name,"rank":rank,"files":changed,"score":result.get("overall_score"),"updates_required":result.get("updates_required"),"summary":result.get("summary"),"live_urls":live_urls},indent=2),encoding="utf-8")
    sheet("updateStatus",post=True,rank=int(rank),researchStatus="Audited",updatesRequired=str(result.get("updates_required","")))
    print(f"AUDITED {name} | files={','.join(changed)} | score={result.get('overall_score')}")
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        print(f"::error::{e}")
        try:
            if 'rank' in locals() and rank:
                sheet("updateStatus",post=True,rank=int(rank),researchStatus="Audit Failed",updatesRequired=str(e))
        except Exception: pass
        sys.exit(1)
