from pathlib import Path
from bs4 import BeautifulSoup
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"404.html"}

def trim_words(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    if len(s) <= n: return s
    x = s[:n+1]
    if " " in x: x = x[:x.rfind(" ")]
    return x.rstrip(" ,:;-|&") + "…"

def title_fix(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    if 30 <= len(s) <= 65: return s
    if len(s) > 65:
        parts = re.split(r"\s+(?:&|\||-)\s+", s)
        while len(parts) > 1 and len(" & ".join(parts[:-1])) >= 30 and len(s) > 65:
            s = " & ".join(parts[:-1]).strip()
            parts = parts[:-1]
        return trim_words(s, 65)
    for suffix in (" | CollegeDecoded", " | College Guide"):
        x = s + suffix
        if len(x) <= 65: return x
    return trim_words(s + " | CollegeDecoded", 65)

def desc_fix(s):
    s = re.sub(r"\s+", " ", s or "").strip()
    if 120 <= len(s) <= 170: return s
    if len(s) > 170: return trim_words(s, 165)
    for add in (" Check admission, fees, eligibility and placements.",
                 " Get admission, fees, eligibility and placement details.",
                 " Includes admission, fees, eligibility, cutoff and placements."):
        x = s + add
        if 120 <= len(x) <= 170: return x
    return trim_words(s + " Check admission, fees, eligibility and placements.", 165)

changed = []
for p in sorted(ROOT.glob("*.html")):
    if p.name in SKIP: continue
    raw = p.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    t = soup.find("title")
    ds = soup.find_all("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if not t or not ds: continue
    ot, od = t.get_text(" ", strip=True), ds[0].get("content", "")
    nt, nd = title_fix(ot), desc_fix(od)
    if (nt, nd) == (ot, od): continue
    t.string = nt
    ds[0]["content"] = nd
    p.write_text(str(soup), encoding="utf-8")
    changed.append(p.name)
print(f"Updated {len(changed)} pages")
