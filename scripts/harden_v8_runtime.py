#!/usr/bin/env python3
"""Apply V8.1 QA/revision hardening at workflow runtime.

This helper patches only the standalone V8 agent. It does not read, import,
execute or follow AGENTS.md or any other repository agent configuration.
"""
from pathlib import Path

P = Path("scripts/independent_college_content_agent_v8.py")
s = P.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Deterministic QA hardening
# ---------------------------------------------------------------------------
a = s.index("def audit(")
b = s.index("\ndef write_report", a)
new_audit = '''def audit(html, page, official_url, existing, filename):
    soup=BeautifulSoup(html,"html.parser"); textv=soup.get_text(" ",strip=True); low=textv.lower(); issues=[]; score=0
    ptype=str(page.get("type","")).lower()
    required_generated_sections=7 if ptype=="placement" else 8
    actual_generated_sections=len([x for x in (page.get("sections") or []) if isinstance(x,dict) and str(x.get("title","")).strip()])

    if len(textv)>=7000: score+=12
    elif len(textv)>=5500: score+=10
    elif len(textv)>=4000: score+=8
    elif len(textv)>=3000: score+=6
    elif len(textv)>=2000: score+=4
    else: issues.append("content too thin")
    qhits=sum(k in low for k in {"admission","eligibility","fee","selection","cutoff","curriculum","placement","faq"})
    score+=min(8,qhits)
    tables=len(soup.find_all("table"))
    if tables>=2: score+=5
    elif tables==1: score+=3
    faq_count=len(soup.select(".faq-item"))
    if faq_count>=5: score+=5
    else: issues.append(f"fewer than 5 FAQs ({faq_count}/5)")
    if actual_generated_sections<required_generated_sections:
        issues.append(f"insufficient content sections ({actual_generated_sections}/{required_generated_sections})")

    arch_checks={
        "header/nav": bool(soup.select_one("header .navbar .nav-links")),
        "hero": bool(soup.select_one(".hero .hero-container h1")),
        "quick facts": len(soup.select(".quick-fact"))==4,
        "desktop sidebar": bool(soup.select_one(".page-layout .sidebar .sidebar-card")),
        "mobile on-page navigation": bool(soup.select_one(".mobile-on-page")),
        "section structure": len(soup.select(".main-section")) >= required_generated_sections+3,
        "answer box": bool(soup.select_one(".answer-box")),
        "CTA": bool(soup.select_one(".cta")),
        "official sources": bool(soup.select_one(".official-links .official-link")),
    }
    score+=sum(2 for x in arch_checks.values() if x)
    failed_arch=[name for name,ok in arch_checks.items() if not ok]
    if failed_arch: issues.append("architecture failures: "+", ".join(failed_arch))

    tech_checks={
        "single H1": len(soup.find_all("h1"))==1,
        "title": bool(soup.title),
        "meta description": bool(soup.find("meta",attrs={"name":"description"})),
        "canonical": bool(soup.find("link",rel="canonical")),
        "OG title": bool(soup.find("meta",attrs={"property":"og:title"})),
        "OG description": bool(soup.find("meta",attrs={"property":"og:description"})),
        "JSON-LD": bool(soup.find("script",attrs={"type":"application/ld+json"})),
        "viewport": bool(soup.find("meta",attrs={"name":"viewport"})),
        "stylesheet": bool(soup.find("link",href=re.compile(r"college-page\\.css"))),
    }
    score+=sum(2 for x in tech_checks.values() if x)
    failed_tech=[name for name,ok in tech_checks.items() if not ok]
    if failed_tech: issues.append("technical SEO failures: "+", ".join(failed_tech))

    domain=urlparse(official_url).netloc.lower().replace("www.","")
    src=[a.get("href") for a in soup.select(".official-link a[href]")]
    official=[u for u in src if urlparse(u).netloc.lower().replace("www.","")==domain]
    if len(official)>=4: score+=15
    elif len(official)>=2: score+=12
    elif official: score+=6
    else: issues.append("no official source links")

    if re.search(r"lorem ipsum|placeholder|insert here|xxx",textv,re.I): issues.append("placeholder content")
    if any(x in low for x in ("₹0","rs. 0","100% guaranteed")): issues.append("placeholder/unsupported claim")
    internal=[]
    for aa in soup.find_all("a",href=True):
        h=aa["href"]
        if h.startswith("/") and not h.startswith("//"): internal.append(h.lstrip("/"))
    broken=[x for x in internal if Path(ROOT/x).name not in existing and x!=filename]
    if broken: issues.append("broken internal links: "+", ".join(broken[:4]))
    critical_terms=("placeholder content","placeholder/unsupported claim","no official source links","technical SEO failures","architecture failures","insufficient content sections","broken internal links")
    critical=any(any(term in issue for term in critical_terms) for issue in issues)
    return min(score,100),issues,critical
'''
s = s[:a] + new_audit + s[b:]

# ---------------------------------------------------------------------------
# Compact structured-content revision
# ---------------------------------------------------------------------------
marker = "\ndef main():\n"
if "def revise_page(" not in s:
    revision = '''\ndef revise_page(page, college, rank, official_url, issues):\n    """Repair structured content without resending the full research corpus."""\n    compact=json.dumps(page,ensure_ascii=False)\n    issue_text=json.dumps(issues,ensure_ascii=False)\n    ptype=str(page.get("type","")).lower()\n    minimum=7 if ptype=="placement" else 8\n    prompt=f"""You are revising ONE structured MBA admissions page after deterministic QA.\nCOLLEGE: {college}\nRANK: {rank}\nOFFICIAL DOMAIN: {official_url}\nPAGE TYPE: {ptype}\n\nQA FAILURES TO FIX:\n{issue_text}\n\nCURRENT PAGE JSON:\n{compact}\n\nREPAIR RULES:\n- Return JSON exactly as {{\\"pages\\":[one page object]}}.\n- Preserve the page type and college identity.\n- Add or repair substantive student-useful content; do not add filler.\n- The page must contain at least {minimum} meaningful content sections in the `sections` array.\n- Keep at least 5 real, college-specific FAQs.\n- Keep exactly 4 quick facts.\n- Use only information already present in the current page JSON; do not invent facts, dates, fees, salaries, recruiters, cutoffs or programme details.\n- If a fact is unsupported or uncertain, write \\\"Not published by the official source\\\" instead of guessing.\n- Keep tables where useful and improve missing decision-support detail.\n- Do not output HTML or commentary.\n"""\n    return gemini(prompt,tokens=18000)\n'''
    s = s.replace(marker, revision + marker, 1)

# ---------------------------------------------------------------------------
# Gemini reliability hardening
# ---------------------------------------------------------------------------
# Replace the model client with a diagnostic, retry-aware implementation. This
# keeps the agent on GenerateContent but makes 429/5xx and malformed responses
# visible instead of collapsing into the generic "Gemini request failed" error.
ga = s.index("def gemini(")
gb = s.index("\ndef read_master", ga)
new_gemini = '''def gemini(prompt, tokens=30000):\n    if not API_KEY:\n        raise RuntimeError("GEMINI_API_KEY is missing")\n    endpoint=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"\n    payload={"contents":[{"role":"user","parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.12,"maxOutputTokens":tokens,"responseMimeType":"application/json"}}\n    headers={"x-goog-api-key":API_KEY,"Content-Type":"application/json"}\n    last_error=""\n    for attempt in range(6):\n        try:\n            r=session.post(endpoint,json=payload,headers=headers,timeout=180)\n            if r.status_code in (429,500,502,503,504):\n                retry_after=r.headers.get("Retry-After")\n                try: wait=float(retry_after) if retry_after else min(60,8*(2**attempt))\n                except ValueError: wait=min(60,8*(2**attempt))\n                print(f"Gemini transient HTTP {r.status_code}; retry {attempt+1}/6 in {wait:.1f}s")\n                last_error=f"HTTP {r.status_code}: {r.text[:500]}"\n                time.sleep(wait)\n                continue\n            if not r.ok:\n                detail=r.text[:1200]\n                raise RuntimeError(f"Gemini HTTP {r.status_code}: {detail}")\n            try:\n                body=r.json()\n                raw=body["candidates"][0]["content"]["parts"][0]["text"]\n                return json.loads(raw)\n            except (KeyError,IndexError,TypeError,ValueError) as exc:\n                last_error=f"Gemini response parse failure: {exc}; body={r.text[:1000]}"\n                if attempt<5:\n                    print(last_error)\n                    time.sleep(min(30,5*(attempt+1)))\n                    continue\n                raise RuntimeError(last_error)\n        except requests.RequestException as exc:\n            last_error=f"Gemini network error: {type(exc).__name__}: {exc}"\n            if attempt>=5: raise RuntimeError(last_error) from exc\n            wait=min(60,8*(2**attempt))\n            print(f"{last_error}; retry {attempt+1}/6 in {wait:.1f}s")\n            time.sleep(wait)\n    raise RuntimeError(last_error or "Gemini request failed after 6 attempts")\n'''
s=s[:ga]+new_gemini+s[gb:]

# Replace the old hard-coded PGP navigation target.
s=s.replace('<a href="pgp.html">PGP</a>', '<a href="index.html">Programmes</a>')

P.write_text(s,encoding="utf-8")
print("V8.1 hardening + Gemini reliability patch applied")
