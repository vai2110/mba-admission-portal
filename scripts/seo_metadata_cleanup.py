from pathlib import Path
import re
import html
import json
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"404.html"}

TITLE_OVERRIDES = {
    "top-mba-colleges-in-india.html": "Top MBA Colleges India: NIRF 2025 | CollegeDecoded",
    "cat.html": "CAT 2026: Dates, Syllabus & Eligibility | CollegeDecoded",
    "iim-bangalore.html": "IIM Bangalore MBA 2027: Fees & CAT | CollegeDecoded",
    "iim-bangalore-mba.html": "IIM Bangalore PGP 2027: Fees & CAT | CollegeDecoded",
    "iim-bangalore-pgpba.html": "IIM Bangalore PGPBA 2027: CAT & Fees | CollegeDecoded",
    "iim-bangalore-epgp.html": "IIM Bangalore EPGP 2027-28: Fees | CollegeDecoded",
    "iim-bangalore-pgpem.html": "IIM Bangalore PGPEM 2027-29: Fees | CollegeDecoded",
    "iim-bangalore-placements.html": "IIM Bangalore Placements 2026 | CollegeDecoded",
    "iim-visakhapatnam.html": "IIM Visakhapatnam MBA 2027 | CollegeDecoded",
    "iim-visakhapatnam-executive-master-of-business-administration-emba.html": "IIM Visakhapatnam EMBA 2027 | CollegeDecoded",
    "jmi-tourism-and-hospitality-management.html": "JMI Tourism & Hospitality Management | CollegeDecoded",
}
DESCRIPTION_OVERRIDES = {
    "top-mba-colleges-in-india.html": "Compare NIRF 2025 Management institutions by rank, city, fees, placements and admission links. Explore CollegeDecoded profiles and verify details before applying.",
    "cat.html": "CAT 2026 is scheduled for 29 November 2026. Check eligibility, registration, exam pattern, syllabus, fees, cutoffs and the IIM admission process.",
    "iim-bangalore.html": "IIM Bangalore MBA admission 2027: PGP, PGPBA, EPGP and PGPEM eligibility, CAT cutoff, fees, admission dates, placements and official links.",
    "iim-bangalore-mba.html": "IIM Bangalore PGP MBA 2027: eligibility, CAT selection process, fees, curriculum, admission timeline, placements and official programme links.",
    "iim-bangalore-pgpba.html": "IIM Bangalore PGPBA 2027-29: eligibility, CAT cutoff, selection process, fees, curriculum, internships, placements and official admission dates.",
    "iim-bangalore-epgp.html": "IIM Bangalore EPGP 2027-28: eligibility, GMAT/GRE, work experience, admission rounds, fees, curriculum, immersion and placement outcomes.",
    "iim-bangalore-pgpem.html": "IIM Bangalore PGPEM 2027-29: eligibility, six-year work experience requirement, CAT/GMAT/GRE/IIMB Test, fees, weekend format and career outcomes.",
    "iim-bangalore-placements.html": "IIM Bangalore placements 2026: official PGP and PGPBA salary data, recruiters, consulting and technology roles, offer trends and median salary comparison.",
}

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def trim_words(s, n):
    s = clean(s)
    if len(s) <= n:
        return s
    words = s.split()
    result = ""
    for word in words:
        candidate = (result + " " + word).strip()
        if len(candidate) > n:
            break
        result = candidate
    return result.rstrip(" ,:;-|&")


def slug_title(slug):
    acronyms = {
        "iim": "IIM", "iit": "IIT", "nit": "NIT", "mba": "MBA",
        "pgp": "PGP", "pgdm": "PGDM", "pgpx": "PGPX", "pgpem": "PGPEM",
        "pgpba": "PGPBA", "emba": "EMBA", "btech": "BTech", "bba": "BBA",
        "bcom": "BCom", "bca": "BCA", "mca": "MCA", "mtech": "MTech",
        "xat": "XAT", "cat": "CAT", "nmat": "NMAT", "cmat": "CMAT",
        "snap": "SNAP", "mat": "MAT", "fms": "FMS", "jmi": "JMI",
        "ibs": "IBS", "mdi": "MDI", "xlri": "XLRI", "spjimr": "SPJIMR",
    }
    return " ".join(acronyms.get(word.lower(), word.capitalize()) for word in slug.split("-") if word)


def title_fix(s, slug=""):
    s = html.unescape(clean(s))
    s = re.sub(r"(?:…|\.{3})\s*$", "", s).rstrip(" ,:;-|&")
    s = re.sub(r"\s*\|\s*CollegeDecoded\s*$", "", s, flags=re.I)
    generic = {
        "post graduate programme (pgp)",
        "department of tourism and hospitality management",
        "executive master of business administration (emba)",
    }
    if not s or s.lower() in generic:
        s = slug_title(slug)
    suffix = " | CollegeDecoded"
    max_base = 60 - len(suffix)
    s = trim_words(s, max_base)
    return (s or slug_title(slug)[:max_base]).rstrip(" ,:;-|&") + suffix


def description_fix(s, title):
    s = html.unescape(clean(s))
    s = re.sub(r"(?:…|\.{3})\s*$", "", s).rstrip(" ,:;-|&")
    s = re.sub(
        r"\s*(?:Check admission, fees, eligibility and placements\.?|Get admission, fees, eligibility and placement details\.?|Includes admission, fees, eligibility, cutoff and placements\.?)\s*$",
        "",
        s,
        flags=re.I,
    ).strip()
    s = re.sub(r"\s+", " ", s)
    if not s:
        s = title.replace(" | CollegeDecoded", "") + ": programme details, eligibility and official admission information."
    return trim_words(s, 155).rstrip(" ,:;-|&")


def meta_tags(raw):
    return list(re.finditer(r"<meta\b[^>]*>", raw, flags=re.I))

def attr(tag, name):
    m = re.search(rf"\b{name}\s*=\s*([\"'])(.*?)\1", tag, flags=re.I)
    return m.group(2) if m else ""

def set_attr(tag, name, value):
    pattern = rf"(\b{name}\s*=\s*)([\"'])(.*?)\2"
    if re.search(pattern, tag, flags=re.I):
        return re.sub(pattern, lambda m: f"{m.group(1)}{m.group(2)}{value}{m.group(2)}", tag, count=1, flags=re.I)
    return tag[:-2] + f' {name}="{value}">' if tag.endswith("/>") else tag[:-1] + f' {name}="{value}">'

def is_description(tag):
    return bool(re.search(r'\bname\s*=\s*[\"\']description[\"\']', tag, flags=re.I))

def has_noindex(raw):
    return bool(re.search(r'<meta\b[^>]*\bname\s*=\s*[\"\']robots[\"\'][^>]*\bcontent\s*=\s*[\"\'][^\"\']*noindex', raw, flags=re.I))

changed = []
for path in sorted(ROOT.rglob("*.html")):
    if path.name in SKIP or any(part in {".git", "node_modules", ".github", ".vercel"} for part in path.parts):
        continue
    raw = path.read_text(encoding="utf-8", errors="replace")
    if has_noindex(raw):
        continue

    title_match = re.search(r"<title\b[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
    if not title_match:
        continue

    old_title = clean(re.sub(r"<[^>]+>", " ", title_match.group(1)))
    new_title = title_fix(TITLE_OVERRIDES.get(path.name, old_title), path.stem)
    updated = raw[:title_match.start()] + f"<title>{html.escape(new_title, quote=False)}</title>" + raw[title_match.end():]

    descriptions = [m for m in meta_tags(updated) if is_description(m.group(0))]
    old_description = attr(descriptions[0].group(0), "content") if descriptions else ""
    new_description = description_fix(DESCRIPTION_OVERRIDES.get(path.name, old_description), new_title)

    if descriptions:
        first = descriptions[0]
        new_tag = set_attr(first.group(0), "content", html.escape(new_description, quote=True))
        updated = updated[:first.start()] + new_tag + updated[first.end():]
        descriptions = [m for m in meta_tags(updated) if is_description(m.group(0))]
        for match in reversed(descriptions[1:]):
            updated = updated[:match.start()] + updated[match.end():]
    else:
        updated = updated.replace("</title>", f'</title>\n<meta name="description" content="{html.escape(new_description, quote=True)}">', 1)

    # Normalize canonical URLs and keep all social metadata aligned with the page.
    canon_match = re.search(r"<link\b[^>]*rel\s*=\s*['\"]canonical['\"][^>]*href\s*=\s*['\"]([^'\"]+)", updated, flags=re.I)
    canonical = canon_match.group(1) if canon_match else f"https://collegedecoded.in/{path.stem}"
    if canonical.startswith("https://collegedecoded.in/") and canonical.endswith(".html"):
        canonical = canonical[:-5]
    canonical_tag = re.search(r"<link\b[^>]*rel\s*=\s*['\"]canonical['\"][^>]*>", updated, flags=re.I)
    canonical_html = f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">'
    if canonical_tag:
        updated = updated[:canonical_tag.start()] + canonical_html + updated[canonical_tag.end():]
    else:
        updated = updated.replace("</head>", canonical_html + "\n</head>", 1)

    def upsert_meta_content(raw, key, value, content):
        pattern = re.compile(rf'<meta\b(?=[^>]*\b{key}\s*=\s*["\']{re.escape(value)}["\'])[^>]*>', flags=re.I | re.S)
        match = pattern.search(raw)
        safe = html.escape(content, quote=True)
        if match:
            tag = match.group(0)
            if re.search(r'\bcontent\s*=', tag, flags=re.I):
                tag = re.sub(r'(\bcontent\s*=\s*)(["\']).*?\2', lambda m: m.group(1) + m.group(2) + safe + m.group(2), tag, count=1, flags=re.I | re.S)
            else:
                tag = tag[:-1] + f' content="{safe}">'
            return raw[:match.start()] + tag + raw[match.end():]
        return raw.replace("</head>", f'<meta {key}="{value}" content="{safe}">\n</head>', 1)

    for key, value, content in [
        ("property", "og:title", new_title),
        ("property", "og:description", new_description),
        ("property", "og:url", canonical),
        ("property", "og:type", "website"),
        ("property", "og:locale", "en_IN"),
        ("name", "twitter:card", "summary_large_image"),
        ("name", "twitter:title", new_title),
        ("name", "twitter:description", new_description),
    ]:
        updated = upsert_meta_content(updated, key, value, content)

    # Prefer a verified page-specific first-party image when one exists.
    # Otherwise use the homepage hero as the safe fallback.
    image_candidates = [
        ROOT / "assets" / "og" / f"{path.stem}.webp",
        ROOT / "assets" / "og" / f"{path.stem}.jpg",
        ROOT / "assets" / "college-images" / f"{path.stem}.webp",
        ROOT / "assets" / "college-images" / f"{path.stem}.jpg",
        ROOT / "assets" / "colleges" / f"{path.stem}.webp",
        ROOT / "assets" / "colleges" / f"{path.stem}.jpg",
    ]
    social_image = next((candidate for candidate in image_candidates if candidate.is_file()), None)
    if social_image is None and path.stem in {"iim-ahmedabad-pgpx", "iim-ahmedabad-mba-pgpx", "iim-ahmedabad-mba"}:
        candidate = ROOT / "assets" / "IIM Ahmedabad PGP Admission 2027-29.png"
        if candidate.is_file():
            social_image = candidate
    if social_image is None:
        social_image = ROOT / "assets" / "homepage" / "hero.webp"
    image_url = "https://collegedecoded.in/" + quote(social_image.relative_to(ROOT).as_posix(), safe="/")
    updated = upsert_meta_content(updated, "property", "og:image", image_url)
    updated = upsert_meta_content(updated, "name", "twitter:image", image_url)

    # Keep structured data synchronized in one pass. Replacing strings using
    # offsets from a pre-mutation finditer list can corrupt later tags when an
    # earlier JSON-LD block changes length.
    def sync_schema(match):
        attrs, body = match.group(1), match.group(2)
        if not re.search(r'type\s*=\s*["\']application/ld\+json["\']', attrs, flags=re.I):
            return match.group(0)
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            return match.group(0)

        graph = payload.get("@graph") if isinstance(payload, dict) else None
        nodes = graph if isinstance(graph, list) else [payload]
        webpage = next((node for node in nodes if isinstance(node, dict) and node.get("@type") == "WebPage"), None)
        if webpage:
            webpage.update({"@id": canonical + "#webpage", "url": canonical, "name": new_title, "description": new_description, "inLanguage": "en-IN"})
        breadcrumb = next((node for node in nodes if isinstance(node, dict) and node.get("@type") == "BreadcrumbList"), None)
        if breadcrumb:
            breadcrumb["@id"] = canonical + "#breadcrumb"
            breadcrumb["itemListElement"] = [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://collegedecoded.in/"},
                {"@type": "ListItem", "position": 2, "name": new_title, "item": canonical},
            ]
        return f'<script{attrs}>{json.dumps(payload, ensure_ascii=False)}</script>'

    updated = re.sub(r'<script\b([^>]*)>(.*?)</script>', sync_schema, updated, flags=re.I | re.S)

    if not re.search(r"<script\b[^>]*type\s*=\s*['\"]application/ld\+json['\"]", updated, flags=re.I):
        import json
        schema = json.dumps({"@context":"https://schema.org","@type":"WebPage","name":new_title,"description":new_description,"url":canonical}, ensure_ascii=False)
        updated = updated.replace("</head>", f'<script type="application/ld+json">{schema}</script>\n</head>', 1)

    if updated != raw:
        path.write_text(updated, encoding="utf-8")
        changed.append(path.name)

print(f"SEO metadata cleanup updated {len(changed)} pages")
