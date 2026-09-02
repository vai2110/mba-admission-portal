import json, os, re, subprocess
from pathlib import Path
from openai import OpenAI
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data" / "college-queue.csv"
STATE = ROOT / "data" / "college-production-state.json"
CSS = ROOT / "college-page.css"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
DONE = "Created + Audited"

PAGE_COLS = ["Overview Page", "Placement Page", "Course Page 1", "Course Page 2", "Course Page 3"]

def slugify(s):
    s = s.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def load_queue():
    import csv
    with QUEUE.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"legacy_completed_ranks": list(range(1,22)), "colleges": {}, "outside_queue": {}}

def save_state(state):
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def first_pending(queue, state):
    legacy = {int(x) for x in state.get("legacy_completed_ranks", [])}
    for row in queue:
        rank = int(row["rank"])
        if rank in legacy:
            continue
        rec = state.setdefault("colleges", {}).setdefault(str(rank), {})
        if any(rec.get(c) != DONE for c in PAGE_COLS):
            return row
    return None

def ask(client, prompt, domain):
    r = client.responses.create(
        model=MODEL,
        tools=[{"type":"web_search", "filters":{"allowed_domains":[domain]}, "search_context_size":"high"}],
        input=prompt,
    )
    return r.output_text

def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m: raise ValueError("Model did not return JSON")
    return json.loads(m.group(0))

def validate_html(html):
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("html") is None or soup.find("title") is None or soup.find("h1") is None:
        raise ValueError("Generated page missing html/title/h1")
    if not soup.find("meta", attrs={"name":"description"}):
        raise ValueError("Generated page missing meta description")
    if not soup.find("link", attrs={"rel":"canonical"}):
        raise ValueError("Generated page missing canonical")
    if html.lower().count("<html") != 1:
        raise ValueError("Invalid HTML document structure")
    return soup.title.get_text(strip=True)

def commit(message):
    subprocess.run(["git","config","user.name","MBA Portal College Agent"],cwd=ROOT,check=True)
    subprocess.run(["git","config","user.email","41898282+github-actions[bot]@users.noreply.github.com"],cwd=ROOT,check=True)
    subprocess.run(["git","add","*.html","data/college-production-state.json"],cwd=ROOT,check=True)
    if subprocess.run(["git","diff","--cached","--quiet"],cwd=ROOT).returncode == 0:
        return False
    subprocess.run(["git","commit","-m",message],cwd=ROOT,check=True)
    subprocess.run(["git","push"],cwd=ROOT,check=True)
    return True

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY GitHub secret is required for autonomous creation.")
    queue = load_queue(); state = load_state(); client = OpenAI()
    row = first_pending(queue, state)
    if not row:
        print("QUEUE COMPLETE")
        return
    rank, college, domain = int(row["rank"]), row["college_name"], row["official_url"].replace("https://","").replace("http://","").split("/")[0]
    rec = state.setdefault("colleges", {}).setdefault(str(rank), {})
    print(f"Next college: #{rank} {college}")

    if "course_plan" not in rec:
        prompt = f'''You are the research planner for an Indian MBA admissions portal. Research ONLY the official website of {college} at {domain}. Identify the three most useful dedicated MBA/management programme pages for prospective students, if at least three exist. Do not invent programmes. If fewer than three relevant programmes exist, return only those that are genuinely offered and set the remaining slots to null. Return JSON only: {{"courses":[{{"name":"...","slug":"..."}},{{"name":"...","slug":"..."}},{{"name":"...","slug":"..."}}]}}. Prefer flagship MBA/PGDM first, then high-demand specialisations or distinct MBA programmes.''' 
        plan = parse_json(ask(client,prompt,domain))
        courses = [c for c in plan.get("courses",[]) if c and c.get("name")][:3]
        while len(courses)<3: courses.append(None)
        rec["course_plan"] = courses
        rec["course_filenames"] = [f"{slugify(college)}-{slugify(c['name'])}.html" if c else None for c in courses]
        save_state(state)

    plan = rec["course_plan"]
    targets = [
        ("Overview Page", f"{slugify(college)}.html", "overview"),
        ("Placement Page", f"{slugify(college)}-placements.html", "placement"),
    ]
    for i,c in enumerate(plan):
        if c: targets.append((f"Course Page {i+1}", rec["course_filenames"][i], "course"))
        else: rec[f"Course Page {i+1}"] = "Not Applicable"

    for col, filename, kind in targets:
        if rec.get(col) == DONE: continue
        rec[col] = "Creating"
        save_state(state)
        page_focus = "overview" if kind=="overview" else "placements" if kind=="placement" else f"the programme {next(c['name'] for c in plan if c and f'{slugify(college)}-{slugify(c[\"name\"])}.html'==filename)}"
        css_ref = "college-page.css"
        prompt = f'''Create one production-ready HTML page for an Indian MBA admissions portal about {college}. Official website: https://{domain}. Page type: {page_focus}. This page will be published directly to GitHub Pages.

Locked content/design standards:
- IIM Ahmedabad is the content-depth benchmark: exact eligibility, selection/admission logic, programme-specific facts, student-intent coverage and official-source discipline.
- SIBM Pune is the architecture/design benchmark: compact text-first hero, clean navigation, strong section hierarchy, useful tables/cards, mobile-first layout.
- Use the reusable stylesheet {css_ref}; link it as <link rel="stylesheet" href="college-page.css">.
- Student-centric simple English. No generic filler.
- Use only facts you can verify from the official website and official documents discovered through web search. Never invent fees, cutoffs, placement numbers, dates, intake or selection weights. If an official figure is unavailable, explicitly say that it is not officially published.
- Include unique SEO title, meta description, canonical, OG/Twitter metadata, one H1, JSON-LD where appropriate, an On This Page navigation, FAQ section, official source links, internal links when they are known, and <hr> between consecutive H2 sections.
- For placements, use latest available official placement information and up to three comparable years; distinguish average/median/highest and placement-year context.
- For overview/admission pages, cover admission cycle, eligibility, application, entrance test, shortlist, selection, fees, popular programmes and placements where officially available.
- For a course page, cover programme overview, duration, eligibility, admission process, curriculum/specialisations, fees, selection, placements/outcomes and FAQs where officially available.
- Do not use external affiliate links, fake testimonials, fake statistics, or fabricated reviews.
- Return JSON only in this shape: {{"html":"FULL HTML DOCUMENT"}}. Do not wrap the JSON in markdown fences.
'''
        try:
            result = parse_json(ask(client,prompt,domain))
            html = result["html"]
            validate_html(html)
            (ROOT/filename).write_text(html,encoding="utf-8")
            rec[col] = "Created — Audit Pending"
            save_state(state)
            print(f"CREATED: {filename}")
        except Exception as e:
            rec[col] = "Needs Review"
            rec.setdefault("errors",[]).append({"page":col,"error":str(e)})
            save_state(state)
            raise
    commit(f"Create {college} college page cluster")

if __name__ == "__main__": main()
