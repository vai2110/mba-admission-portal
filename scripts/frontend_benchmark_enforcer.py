import os
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

# Locked visual contract: IIM Ahmedabad content shell + SIBM Pune compact IA.
CSS_HREF = "college-page.css"
RESPONSIVE_PATCH = """
/* Locked benchmark responsive safeguards */
html{overflow-x:hidden}
body{overflow-x:hidden}
img{max-width:100%;height:auto}
.table-wrapper{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
@media(max-width:720px){
  .hero-container,.page-container,.navbar{width:calc(100% - 20px)}
  .hero h1{font-size:26px;line-height:1.2}
  .hero h2{font-size:13px;line-height:1.5}
  .page-layout{display:block}
  .sidebar{display:none}
  .mobile-on-page{display:block;position:sticky;top:56px;z-index:900}
  .main-section{padding:20px 15px}
  .main-section>h2{font-size:21px}
  .highlight-grid,.programme-grid,.two-column,.official-links,.decision-list{grid-template-columns:1fr}
  table{min-width:620px}
}
"""


def targets():
    return [x.strip() for x in os.getenv("TARGET_PAGES", "").splitlines() if x.strip()]


def ensure_css(soup):
    for link in soup.find_all("link", href=True):
        if link.get("href") == CSS_HREF:
            return False
    link = soup.new_tag("link", rel="stylesheet", href=CSS_HREF)
    # Put shared CSS after page-local styles so the locked benchmark rules win.
    styles = soup.find_all("style")
    if styles:
        styles[-1].insert_after(link)
    elif soup.head:
        soup.head.append(link)
    return True


def ensure_viewport(soup):
    if soup.find("meta", attrs={"name": "viewport"}):
        return False
    if not soup.head:
        return False
    meta = soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1.0"})
    soup.head.insert(0, meta)
    return True


def ensure_responsive_patch(soup):
    for style in soup.find_all("style"):
        if "Locked benchmark responsive safeguards" in (style.get_text() or ""):
            return False
    style = soup.new_tag("style")
    style.string = RESPONSIVE_PATCH
    if soup.head:
        soup.head.append(style)
        return True
    return False


def ensure_mobile_on_page(soup):
    # Existing benchmark pages already have this. Do not manufacture navigation
    # from arbitrary headings because generated anchors are content-specific.
    if soup.select_one(".mobile-on-page"):
        return False
    return False


def ensure_single_h1(soup):
    h1s = soup.find_all("h1")
    if len(h1s) <= 1:
        return False
    # Preserve the first H1; convert later H1s to H2 to keep the page hierarchy valid.
    for h in h1s[1:]:
        h.name = "h2"
    return True


def fix(path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    changes = []
    if ensure_viewport(soup): changes.append("viewport")
    if ensure_css(soup): changes.append("shared CSS")
    if ensure_responsive_patch(soup): changes.append("responsive safeguards")
    if ensure_single_h1(soup): changes.append("single H1")
    if changes:
        path.write_text("<!DOCTYPE html>\n" + str(soup), encoding="utf-8")
    return path.name, changes


def main():
    pages = targets()
    if not pages:
        raise SystemExit("TARGET_PAGES required")
    for name in pages:
        path = (ROOT / name).resolve()
        if path.parent != ROOT or not path.exists() or path.suffix.lower() != ".html":
            continue
        filename, changes = fix(path)
        print(f"FRONTEND BENCHMARK {'UPDATED' if changes else 'OK'}: {filename}" + (f" — {', '.join(changes)}" if changes else ""))


if __name__ == "__main__":
    main()
