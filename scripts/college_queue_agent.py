import csv
import json
import os
import re
import subprocess
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'data/college-queue.csv'
STATE = ROOT / 'data/college-production-state.json'
MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite')
DONE = 'Created + Audited'
COLS = ['Overview Page', 'Placement Page', 'Course Page 1', 'Course Page 2', 'Course Page 3']

KEYWORDS = {
    'mba': 12, 'management': 10, 'admission': 10, 'programme': 8, 'program': 8,
    'executive': 9, 'fees': 8, 'fee': 8, 'placement': 10, 'placements': 10,
    'brochure': 8, 'prospectus': 8, 'curriculum': 6, 'eligibility': 7,
    'selection': 7, 'application': 6, 'hostel': 4, 'annual-report': 5,
    'nirf': 4, 'corporate': 4, 'school': 4, 'iim': 3
}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', ' and ')).strip('-')


def loadq():
    with QUEUE.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def loads():
    return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {
        'legacy_completed_ranks': list(range(1, 22)), 'colleges': {}
    }


def saves(s):
    STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def pending(q, s):
    legacy = {int(x) for x in s.get('legacy_completed_ranks', [])}
    unheld = []
    held = []
    for row in q:
        rank = int(row['rank'])
        if rank in legacy:
            continue
        rec = s.setdefault('colleges', {}).setdefault(str(rank), {})
        if all(rec.get(c) in (DONE, 'Not Applicable') for c in COLS):
            continue
        if rec.get('held'):
            held.append(row)
        else:
            unheld.append(row)
    return (unheld + held)[0] if (unheld or held) else None


def fetch_url(url, timeout=15):
    req = Request(url, headers={'User-Agent': 'MBA-Admission-Portal-Research/1.0'})
    with urlopen(req, timeout=timeout) as r:
        content_type = r.headers.get('Content-Type', '').lower()
        data = r.read(2_000_000)
        return content_type, data


def clean_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'svg']):
        tag.decompose()
    return re.sub(r'\s+', ' ', soup.get_text(' ', strip=True)).strip()


def score_url(url):
    path = urlparse(url).path.lower()
    return sum(weight for word, weight in KEYWORDS.items() if word in path)


def crawl_official_site(start_url, domain, max_pages=16):
    """Collect a compact research pack from the official domain only."""
    queue = deque([start_url.rstrip('/')])
    seen = set()
    candidates = []
    docs = []

    while queue and len(seen) < max_pages:
        url = urldefrag(queue.popleft())[0]
        parsed = urlparse(url)
        if parsed.netloc.lower() != domain.lower() or url in seen:
            continue
        if any(x in parsed.path.lower() for x in ['/login', '/logout', '/search']):
            continue
        seen.add(url)
        last_error = None
        for attempt in range(3):
            try:
                ctype, data = fetch_url(url)
                break
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        else:
            print(f'WARN official fetch failed after retries: {url}: {last_error}')
            continue

        if 'application/pdf' in ctype or parsed.path.lower().endswith('.pdf'):
            try:
                import io
                reader = PdfReader(io.BytesIO(data))
                text = '\n'.join((p.extract_text() or '') for p in reader.pages[:12])
                text = re.sub(r'\s+', ' ', text).strip()
                if text:
                    docs.append({'url': url, 'title': parsed.path.rsplit('/', 1)[-1], 'text': text[:7000]})
            except Exception:
                pass
            continue

        if 'text/html' not in ctype and not data.lstrip().startswith(b'<!DOCTYPE'):
            continue
        html = data.decode('utf-8', errors='ignore')
        text = clean_text(html)
        if text:
            title = BeautifulSoup(html, 'html.parser').title
            title = title.get_text(' ', strip=True) if title else url
            candidates.append({'url': url, 'title': title, 'text': text[:6000], 'score': score_url(url)})

        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = urldefrag(urljoin(url, a['href']))[0]
            p = urlparse(href)
            if p.netloc.lower() != domain.lower() or p.scheme not in ('http', 'https'):
                continue
            if p.path.lower().endswith('.pdf') or any(k in href.lower() for k in KEYWORDS):
                links.append((score_url(href), href))
        for _, href in sorted(set(links), reverse=True)[:20]:
            if href not in seen:
                queue.append(href)

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return (candidates[:12] + docs[:4])[:16]


def gemini_json(prompt, max_output_tokens=12000):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise SystemExit('GEMINI_API_KEY GitHub secret is required for autonomous creation.')

    endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'responseMimeType': 'application/json',
            'temperature': 0.2,
            'maxOutputTokens': max_output_tokens
        }
    }
    body = json.dumps(payload).encode('utf-8')
    last = None
    for attempt in range(3):
        try:
            req = Request(endpoint, data=body, method='POST', headers={
                'Content-Type': 'application/json',
                'x-goog-api-key': api_key,
                'User-Agent': 'MBA-Admission-Portal-Production/1.0'
            })
            with urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode('utf-8'))
            return data['candidates'][0]['content']['parts'][0]['text']
        except HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='ignore')
            last = f'HTTP {exc.code}: {detail[:1200]}'
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(8 * (attempt + 1))
                continue
            raise RuntimeError(f'Gemini API request failed: {last}') from exc
        except (URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
            last = str(exc)
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f'Gemini API request failed: {last}') from exc
    raise RuntimeError(f'Gemini API request failed: {last}')


def json_out(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?', '', text).strip()
    text = re.sub(r'```$', '', text).strip()
    m = re.search(r'\{.*\}', text, re.S)
    if not m:
        raise ValueError('Gemini did not return JSON')
    return json.loads(m.group(0))


def validate(html):
    soup = BeautifulSoup(html, 'html.parser')
    if not soup.find('html') or not soup.find('title') or not soup.find('h1'):
        raise ValueError('Missing html/title/h1')
    if not soup.find('meta', attrs={'name': 'description'}):
        raise ValueError('Missing meta description')
    if not soup.find('link', attrs={'rel': 'canonical'}):
        raise ValueError('Missing canonical')
    if html.lower().count('<html') != 1:
        raise ValueError('Invalid HTML structure')


def commit(msg):
    subprocess.run(['git', 'config', 'user.name', 'MBA Portal College Agent'], cwd=ROOT, check=True)
    subprocess.run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'], cwd=ROOT, check=True)
    subprocess.run(['git', 'add', '*.html', 'data/college-production-state.json'], cwd=ROOT, check=True)
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode:
        return
    subprocess.run(['git', 'commit', '-m', msg], cwd=ROOT, check=True)
    subprocess.run(['git', 'push'], cwd=ROOT, check=True)


def main():
    if not os.getenv('GEMINI_API_KEY'):
        raise SystemExit('GEMINI_API_KEY GitHub secret is required for autonomous creation.')

    q = loadq()
    s = loads()
    row = pending(q, s)
    if not row:
        print('QUEUE COMPLETE')
        return

    rank = int(row['rank'])
    college = row['college_name']
    official_url = row['official_url'].rstrip('/')
    domain = urlparse(official_url).netloc
    rec = s.setdefault('colleges', {}).setdefault(str(rank), {})
    if rec.get('held'):
        print(f'Revisiting previously held college: #{rank} {college}')
        rec.pop('held', None)
        rec.pop('hold_reason', None)
        rec.pop('hold_timestamp_utc', None)
        saves(s)
    print(f'Next college: #{rank} {college}')

    if 'research_pack' not in rec:
        print(f'Researching official domain: {official_url}')
        sources = crawl_official_site(official_url, domain)
        if not sources:
            raise RuntimeError(f'Could not retrieve usable public content from official domain {domain}')

        research_text = '\n\n'.join(
            f"SOURCE URL: {x['url']}\nTITLE: {x['title']}\nCONTENT: {x['text']}"
            for x in sources
        )[:60000]

        prompt = f'''You are the research controller for an Indian MBA admissions portal.
College: {college}
Official domain: {domain}

The material below was fetched directly from the college's official domain. Use ONLY this material. Do not add facts from memory or third-party sources.

Determine the actual substantial MBA/management programmes that deserve dedicated pages. Exclude PhD/doctoral programmes, certificates, short courses, and quota/category-only pages.

Return JSON with exactly these keys:
{{
  "courses": [{{"name":"..."}}],
  "research_summary": "compact factual summary of admissions, eligibility, selection, fees, placements and programme details",
  "sources": [{{"url":"official URL", "title":"source title", "supports":"what this source supports"}}]
}}

Keep research_summary factual and compact. If a fact is not present in the supplied material, say it is unavailable.

OFFICIAL SOURCE MATERIAL:
{research_text}'''

        plan = json_out(gemini_json(prompt, max_output_tokens=5000))
        courses = [x for x in plan.get('courses', []) if x and x.get('name')][:3]
        rec['course_plan'] = courses
        rec['course_filenames'] = [f"{slug(college)}-{slug(x['name'])}.html" for x in courses]
        while len(rec['course_plan']) < 3:
            rec['course_plan'].append(None)
            rec['course_filenames'].append(None)
        rec['research_pack'] = {
            'summary': plan.get('research_summary', ''),
            'sources': plan.get('sources', []),
            'source_material': research_text
        }
        saves(s)

    targets = [
        ('Overview Page', f'{slug(college)}.html', 'overview'),
        ('Placement Page', f'{slug(college)}-placements.html', 'placement')
    ]
    for i, course in enumerate(rec['course_plan']):
        key = f'Course Page {i+1}'
        if course:
            targets.append((key, rec['course_filenames'][i], 'course'))
        else:
            rec[key] = 'Not Applicable'
    saves(s)

    research = rec['research_pack']
    source_material = research['source_material']
    source_list = '\n'.join(
        f"- {x.get('title','Official source')}: {x.get('url','')} — {x.get('supports','')}"
        for x in research.get('sources', [])
    )

    created_pages = []
    for col, filename, kind in targets:
        if rec.get(col) == DONE:
            continue
        rec[col] = 'Creating'
        saves(s)
        if kind == 'overview':
            focus = 'college overview, MBA admissions and student decision-making'
        elif kind == 'placement':
            focus = 'placements, placement process and year-wise placement outcomes'
        else:
            course_name = next(c['name'] for i, c in enumerate(rec['course_plan']) if c and rec['course_filenames'][i] == filename)
            focus = f'dedicated programme page for {course_name}'

        prompt = f'''Create one production-ready HTML document for an Indian MBA admissions portal about {college}.
Official website: {official_url}
Page focus: {focus}

CRITICAL SOURCE RULE:
Use ONLY the official-domain research material supplied below. Do not invent, infer, estimate or supplement fees, cutoffs, dates, intake, placement numbers, selection weights, eligibility, programme names or other factual claims. If official material does not provide a fact, explicitly say official information is unavailable. Do not cite third-party sources.

LOCKED CONTENT/DESIGN STANDARDS:
- IIM Ahmedabad is the content-depth benchmark: exact eligibility, selection logic, programme facts, student intent and official-source discipline.
- SIBM Pune is the architecture/design benchmark: compact text-first hero, clean navigation, useful tables/cards, clear hierarchy and mobile-first presentation.
- Link college-page.css.
- Simple student-centric English. No generic filler.
- Include unique title, meta description, canonical, OG/Twitter metadata, one H1, relevant JSON-LD, one Quick Answer, On This Page navigation, FAQs, official source links and useful internal links when known.
- Use short keyword-focused H2s and put <hr> between consecutive H2 sections.
- Overview: cover admission, eligibility, application, entrance, shortlist, selection, fees, programmes and placements where official information exists.
- Placement: use the latest official placement data and up to three comparable years where the official material supports it. Never fabricate missing years.
- Course: cover programme overview, duration, eligibility, admission, curriculum/specialisations, fees, selection, outcomes and FAQs where official information exists.
- Do not create PhD, certificate, short-course or quota/category pages.
- The page must be self-contained valid HTML and publish directly to GitHub Pages.

OFFICIAL SOURCE INDEX:
{source_list}

RESEARCH SUMMARY:
{research['summary']}

OFFICIAL SOURCE MATERIAL:
{source_material}

Return JSON only: {{"html":"FULL HTML DOCUMENT"}}. No markdown fences.'''

        try:
            html = json_out(gemini_json(prompt, max_output_tokens=12000))['html']
            validate(html)
            (ROOT / filename).write_text(html, encoding='utf-8')
            rec[col] = 'Created — Audit Pending'
            created_pages.append(filename)
            saves(s)
            print('CREATED', filename)
        except Exception as e:
            rec[col] = 'Needs Review'
            rec.setdefault('errors', []).append({'page': col, 'error': str(e)})
            saves(s)
            raise

    if created_pages:
        rec['created_pages_last_run'] = created_pages
        saves(s)
        commit(f'Create {college} college page cluster')


if __name__ == '__main__':
    main()
