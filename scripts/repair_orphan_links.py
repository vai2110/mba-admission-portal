import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"404.html", "content-audit.html", "college-page-audit-dashboard.html", "github-direct-edit-test.html", "irma-deploy-trigger.html"}
PROTECTED = {"iim-ahmedabad.html", "sibm-pune.html"}

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for k,v in attrs:
                if k.lower() == "href" and v:
                    self.hrefs.append(v); break

def hrefs(html):
    p=Parser(); p.feed(html); p.close(); return p.hrefs

def target(href):
    href = href.strip()
    if not href or href.startswith(("#","http://","https://","mailto:","tel:","javascript:","data:")): return None
    path=(urlsplit(href).path or "/").rstrip("/") or "/"
    raw=path.lstrip("/") if path.startswith("/") else path
    if raw=="" or raw=="/": return "index.html"
    for c in (raw, raw+".html" if not raw.endswith(".html") else raw[:-5], raw+"/index.html"):
        if (ROOT/c).is_file(): return Path(c).as_posix()
    return None

def add_link(source, dest, label):
    path=ROOT/source
    html=path.read_text(encoding="utf-8")
    if re.search(rf'href=["\'](?:https://collegedecoded\\.in)?/?{re.escape(dest[:-5])}(?:\.html)?["\']', html, re.I):
        return False
    block=f'<nav class="seo-related-link" aria-label="Related page"><a href="{dest}">{label}</a></nav>'
    if "seo-related-link" not in html:
        html=re.sub(r"</body>", block+"</body>", html, count=1, flags=re.I)
    else:
        return False
    path.write_text(html,encoding="utf-8"); return True

def label(name):
    return Path(name).stem.replace("-"," ").title()

def main():
    pages=sorted(p.name for p in ROOT.glob("*.html") if p.name not in EXCLUDED)
    page_set=set(pages); incoming=Counter()
    for p in pages:
        for h in hrefs((ROOT/p).read_text(encoding="utf-8")):
            t=target(h)
            if t in page_set: incoming[t]+=1
    orphans=[p for p in pages if incoming[p]==0 and p not in PROTECTED]
    changed=[]
    for orphan in orphans:
        stem=Path(orphan).stem
        candidates=[]
        # Prefer exact college overview for programme/placement pages.
        base=stem
        if base.endswith("-placements"): base=base[:-11]
        # Strip common programme suffixes until an existing overview is found.
        while "-" in base:
            candidate=base+".html"
            if candidate in page_set and candidate != orphan:
                candidates.append(candidate); break
            base=base.rsplit("-",1)[0]
        # If no overview, use a same-prefix sibling.
        if not candidates:
            prefix=stem.rsplit("-",1)[0]
            candidates=[p for p in pages if p.startswith(prefix+"-") and p not in {orphan}][:1]
        # Overview/hub or unmatched pages: homepage is a safe crawlable hub.
        if not candidates and "index.html" in page_set and orphan!="index.html":
            candidates=["index.html"]
        if not candidates: continue
        source=candidates[0]
        if add_link(source, orphan, label(orphan)):
            changed.append((source,orphan))
    css='''<style id="seo-related-link-style">.seo-related-link{margin:18px 0;padding:8px 0;font-size:13px}.seo-related-link a{color:#2563eb;font-weight:600;text-decoration:none}.seo-related-link a:hover{text-decoration:underline}</style>'''
    for p in {s for s,_ in changed}:
        path=ROOT/p; html=path.read_text(encoding="utf-8")
        if "seo-related-link-style" not in html:
            html=re.sub(r"</head>",css+"</head>",html,count=1,flags=re.I); path.write_text(html,encoding="utf-8")
    print(f"Orphan link repair: {len(changed)} links added.")
    for s,d in changed: print(f"- {s} -> {d}")

if __name__=="__main__": main()
