from pathlib import Path
import re

PAGE = Path('mba-colleges-by-location.html')
MARKER = '/* POPULAR_LOCATION_TEMPLATE_V2 */'

CSS = r'''
/* POPULAR_LOCATION_TEMPLATE_V2 */
.location-template{margin:0 auto 30px;padding:0 2px}
.location-template-head{position:relative;margin-bottom:16px;padding-right:245px}
.location-template-head h2{margin:0;color:#102a43;font-size:26px;line-height:1.15;font-weight:900;letter-spacing:-.55px}
.location-template-head h2 span{color:#4438ff}
.location-template-head p{margin:6px 0 0;color:#173f82;font-size:10px;line-height:1.45;font-weight:600}
.location-callout{position:absolute;right:8px;top:-3px;color:#8198d4;font-size:10px;line-height:1.25;font-style:italic;font-weight:700;transform:rotate(-2deg);max-width:150px;text-align:center}
.location-callout:before{content:"↙";position:absolute;left:-25px;bottom:-8px;font-size:28px;font-style:normal;font-weight:400;color:#9ab0e6;transform:rotate(18deg)}
.location-template-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px}
.template-card{position:relative;display:flex;flex-direction:column;min-width:0;min-height:284px;border:1px solid rgba(135,154,194,.22);border-radius:14px;overflow:hidden;cursor:pointer;text-align:left;background:linear-gradient(145deg,var(--soft),#fff 72%);box-shadow:0 5px 14px rgba(31,50,91,.08);transition:transform .2s ease,box-shadow .2s ease}
.template-card:hover{transform:translateY(-4px);box-shadow:0 12px 24px rgba(31,50,91,.15)}
.template-card:focus-visible{outline:3px solid rgba(68,56,255,.3);outline-offset:2px}
.template-card .card-image{position:relative;height:142px;flex:0 0 142px;overflow:hidden}
.template-card .card-image img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .35s ease}
.template-card:hover .card-image img{transform:scale(1.045)}
.template-card .card-image:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(13,31,69,.08) 70%,rgba(13,31,69,.25));pointer-events:none}
.template-card .num{position:absolute;left:12px;top:10px;z-index:3;color:#5573a9;font-size:9px;font-weight:900;letter-spacing:.6px;background:rgba(255,255,255,.78);padding:3px 5px;border-radius:5px}
.template-card .card-copy{padding:12px;display:flex;flex-direction:column;flex:1}
.template-card h3{margin:0 0 4px;color:#092653;font-size:17px;line-height:1.05;font-weight:900;letter-spacing:-.25px}
.template-card .tagline{margin:0;color:#173f82;font-size:9px;line-height:1.35;font-weight:700;min-height:25px;max-width:175px}
.template-card .benefits{display:flex;flex-wrap:wrap;gap:4px 8px;margin-top:8px;padding-top:7px;border-top:1px solid rgba(23,63,130,.10)}
.template-card .benefit{display:inline-flex;align-items:center;gap:3px;color:#173f82;font-size:7px;line-height:1.1;font-weight:800;white-space:nowrap}
.template-card .benefit i{font-style:normal;color:var(--accent);font-size:10px}
.template-card .cta{align-self:flex-start;margin-top:auto;padding:8px 11px;border-radius:7px;background:var(--accent);color:#fff;font-size:9px;line-height:1;font-weight:900;box-shadow:0 4px 9px rgba(23,63,130,.16);display:inline-flex;align-items:center;gap:9px}
.template-card .cta i{font-size:13px;font-style:normal;line-height:1;transition:transform .2s ease}
.template-card:hover .cta i{transform:translateX(3px)}
.template-card:nth-child(1){--soft:#fff6ef;--accent:#2147b8}.template-card:nth-child(2){--soft:#eef7ff;--accent:#293fe0}.template-card:nth-child(3){--soft:#effcfb;--accent:#229866}.template-card:nth-child(4){--soft:#f7efff;--accent:#5a25bc}.template-card:nth-child(5){--soft:#fff7ed;--accent:#f05a13}.template-card:nth-child(6){--soft:#fff3f0;--accent:#bd2529}.template-card:nth-child(7){--soft:#eefaff;--accent:#118bb4}.template-card:nth-child(8){--soft:#f6efff;--accent:#5b2cd5}.template-card:nth-child(9){--soft:#f4fbef;--accent:#438d31}.template-card:nth-child(10){--soft:#fff2f2;--accent:#c93643}
@media(max-width:1000px){.location-template-grid{grid-template-columns:repeat(3,1fr)}.location-template-head{padding-right:190px}}
@media(max-width:760px){.location-template-head{padding-right:0}.location-callout{position:relative;right:auto;top:auto;margin:8px 0 0 28px;text-align:left;max-width:none;display:inline-block}.location-template-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.location-template-head h2{font-size:22px}.location-template-grid{grid-template-columns:1fr}.template-card{min-height:300px}.template-card .card-image{height:150px;flex-basis:150px}}
'''

SECTION = r'''<section class="location-template" aria-labelledby="popular-destination-title">
  <div class="location-template-head">
    <h2 id="popular-destination-title">Where do students commonly look for an <span>MBA?</span></h2>
    <p>Explore India's most popular MBA destinations — top colleges, better career opportunities, vibrant student life and strong industry exposure.</p>
    <div class="location-callout">Find the right city<br>for your MBA journey</div>
  </div>
  <div class="location-template-grid" id="popularGrid" aria-label="Popular MBA destinations"></div>
</section>'''

FUNCTION = r'''function renderPopular(){
const copy={
'Delhi NCR':{tag:"India's career capital<br>with endless opportunities.",benefits:[['🏆','Top recruiters'],['♜','Diverse options'],['◎','Great connectivity']]},
'Mumbai':{tag:"India's financial hub<br>for ambitious minds.",benefits:[['▥','Finance & BFSI'],['◉','Global exposure'],['◎','Dynamic city life']]},
'Bengaluru':{tag:'Where innovation<br>meets opportunity.',benefits:[['▣','Tech & startups'],['♧','Global companies'],['➤','Vibrant culture']]},
'Pune':{tag:'A student-friendly city<br>with a strong MBA ecosystem.',benefits:[['♧','Reputed institutes'],['⌂','Affordable living'],['♙','Great campus life']]},
'Ahmedabad':{tag:'A hub for management<br>and innovation.',benefits:[['🏆','Premier institutes'],['♜','Industry exposure'],['▥','Growing opportunities']]},
'Kolkata':{tag:'A legacy of excellence<br>in management education.',benefits:[['🏆','Rich academic culture'],['♜','Strong alumni network'],['♧','Growing corporate presence']]},
'Chennai':{tag:'A gateway to diverse<br>career opportunities.',benefits:[['♙','Reputed B-schools'],['▥','Industry driven'],['➤','Pleasant living']]},
'Hyderabad':{tag:'A rising hub for business,<br>tech and innovation.',benefits:[['🏆','Top recruiters'],['▣','Startup ecosystem'],['♜','Modern infrastructure']]},
'Lucknow':{tag:'A perfect blend of<br>heritage and opportunities.',benefits:[['♜','Reputed institutes'],['♧','Peaceful environment'],['➤','Growing career options']]},
'Jaipur':{tag:'Where tradition meets<br>modern education.',benefits:[['🏆','Reputed B-schools'],['♜','Student-friendly city'],['➤','Growing opportunities']]}
};
popularGrid.innerHTML=popular.map((p,i)=>{const c=copy[p.name]||{tag:'Explore MBA opportunities.',benefits:[]},v=cityVisuals[p.name]||{};return '<button class="template-card" type="button" data-key="'+esc(p.key)+'"><span class="card-image"><img loading="lazy" src="'+esc(v.image||'')+'" alt="'+esc(p.name+' MBA destination')+'"><span class="num">'+String(i+1).padStart(2,'0')+'</span></span><span class="card-copy"><h3>'+esc(p.name)+'</h3><span class="tagline">'+c.tag+'</span><span class="benefits">'+c.benefits.map(b=>'<span class="benefit"><i>'+b[0]+'</i>'+esc(b[1])+'</span>').join('')+'</span><span class="cta">Explore Popular Colleges <i>→</i></span></span></button>'}).join('');
document.querySelectorAll('.template-card').forEach(btn=>btn.addEventListener('click',()=>showPopular(popular.find(p=>p.key===btn.dataset.key))));
}'''

html = PAGE.read_text(encoding='utf-8')
if MARKER not in html:
    html = html.replace('</head>', '<style>\n' + CSS + '</style>\n</head>', 1)

section_re = re.compile(r'<section>\s*<div class="section-heading">\s*<h2>Where do students commonly look for an MBA\?</h2>.*?</section>\s*<hr>', re.S)
html, n = section_re.subn(SECTION + '\n<hr>', html, count=1)
if n == 0:
    html, n = re.subn(r'<section class="location-template".*?</section>', SECTION, html, count=1, flags=re.S)

func_re = re.compile(r'function renderPopular\(\)\{.*?\}\s*function rankLabel', re.S)
html, nfunc = func_re.subn(FUNCTION + '\nfunction rankLabel', html, count=1)
if nfunc == 0:
    raise SystemExit('Could not locate renderPopular() in mba-colleges-by-location.html')

PAGE.write_text(html, encoding='utf-8')
print(f'updated page: section={n}, renderPopular={nfunc}')
