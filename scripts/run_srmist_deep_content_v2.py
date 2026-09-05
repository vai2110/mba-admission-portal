from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'scripts' / 'srmist_deep_content_v2.py').read_text(encoding='utf-8')
exec(source.split("files={'overview':")[0], globals())

def fixed_page(title,h1,subtitle,kind,body,filename,quick=None):
    q=''
    if isinstance(quick, (list, tuple)) and quick and all(isinstance(x,(list,tuple)) and len(x)==2 for x in quick):
        q='<div class="quick-facts">'+''.join(f'<div class="quick-fact"><span class="quick-fact-label">{a}</span><span class="quick-fact-value">{b}</span></div>' for a,b in quick)+'</div>'
    sources='<section class="main-section" id="sources"><h2>Official Sources</h2><div class="official-links"><div class="official-link"><a href="https://www.srmist.edu.in/" target="_blank" rel="noopener">SRMIST official website ↗</a></div><div class="official-link"><a href="https://www.srmist.edu.in/admission-india/management/" target="_blank" rel="noopener">SRMIST management admissions ↗</a></div><div class="official-link"><a href="srmist-placements.html">SRMIST placement guide</a></div></div></section>'
    return f'''<!DOCTYPE html><html lang="en-IN"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{title}</title><meta name="description" content="{title}. Student-focused guide covering eligibility, admission, fees, cutoff, curriculum, placements and FAQs."/><link rel="canonical" href="https://vai2110.github.io/mba-admission-portal/{filename}"/><link rel="stylesheet" href="college-page.css"/><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"/></head><body><header><div class="navbar"><a class="logo" href="index.html">MBA<span>Portal</span></a><nav class="nav-links"><a href="index.html">Home</a><a href="srm-institute-science-technology.html">SRMIST</a><a href="srmist-placements.html">Placements</a></nav></div></header><section class="hero"><div class="hero-container"><h1>{h1}</h1><h2>{subtitle}</h2><div class="hero-location">SRM Institute of Science and Technology · <a href="https://www.srmist.edu.in/" target="_blank" rel="noopener">Official SRMIST Website ↗</a></div></div></section><div class="page-container">{q}{nav(kind)}{body}{sources}</main></div></div><script>document.querySelectorAll("table").forEach(t=>{{t.classList.add("mobile-fit-table");t.querySelectorAll("tr").forEach(r=>{{[...r.children].forEach((c,i)=>{{const h=t.querySelector("tr").children[i];if(h)c.dataset.label=h.textContent.trim();}});}});}});</script></body></html>'''

globals()['page'] = fixed_page
(ROOT/'srm-institute-science-technology.html').write_text(overview(),encoding='utf-8')
(ROOT/'srmist-placements.html').write_text(placements(),encoding='utf-8')
filenames={'btech-cse':'srmist-btech-cse.html','btech-ai':'srmist-btech-artificial-intelligence.html','btech-it':'srmist-btech-information-technology.html','btech-ece':'srmist-btech-ece.html','mba':'srmist-mba.html','mba-business-analytics':'srmist-mba-business-analytics.html','mba-financial-services-nse':'srmist-mba-financial-services-nse.html','mbbs':'srmist-mbbs.html','mca':'srmist-mca.html'}
for key,filename in filenames.items():
    (ROOT/filename).write_text(course_body(key),encoding='utf-8')
expected=['srm-institute-science-technology.html','srmist-placements.html',*filenames.values()]
for f in expected:
    txt=(ROOT/f).read_text(encoding='utf-8')
    assert txt.count('<h1>')==1, f'{f}: H1 count'
    assert 'On this page' in txt, f'{f}: missing on-page nav'
    assert 'id="faq"' in txt, f'{f}: missing FAQ'
    assert 'id="sources"' in txt, f'{f}: missing sources'
    assert txt.count('<main class="content">')==1 and txt.count('</main>')==1, f'{f}: main wrapper'
print('SRMIST deep-content v2 generated and validated:', len(expected), 'pages')