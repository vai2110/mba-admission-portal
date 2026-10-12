from pathlib import Path
import re
import html
import json

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"404.html", "iim-ahmedabad.html", "sibm-pune.html"}

TITLE_OVERRIDES = {
    "iim-bangalore.html": "IIM Bangalore MBA Admission 2027: Fees, CAT Cutoff & Placements",
    "iim-bangalore-mba.html": "IIM Bangalore MBA 2027: Fees, Eligibility, CAT & Placements",
    "iim-bangalore-pgpba.html": "IIM Bangalore PGPBA Admission 2027: CAT, Fees & Eligibility",
    "iim-bangalore-epgp.html": "IIM Bangalore EPGP Admission 2027-28: Eligibility & Fees",
    "iim-bangalore-pgpem.html": "IIM Bangalore PGPEM Admission 2027-29: Fees, CAT & Eligibility",
    "iim-bangalore-placements.html": "IIM Bangalore Placements 2026: Salary, Recruiters & Offers",
}
DESCRIPTION_OVERRIDES = {
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
    x = s[: max(1, n - 1)]
    if " " in x:
        x = x[: x.rfind(" ")]
    return x.rstrip(" ,:;-|&") + "…"

def title_fix(s):
    s = html.unescape(clean(s))
    if 30 <= len(s) <= 65:
        return s
    if len(s) > 65:
        candidates = re.split(r"\s+(?:\||&|-|–|:)\s+", s)
        while len(candidates) > 1:
            candidate = " & ".join(candidates[:-1]).strip()
            if 30 <= len(candidate) <= 65:
                return candidate
            candidates.pop()
        return trim_words(s, 65)
    suffix = " | CollegeDecoded"
    if len(s) + len(suffix) <= 65:
        return s + suffix
    return trim_words(s + suffix, 65)

def description_fix(s, title):
    s = html.unescape(clean(s))
    if 120 <= len(s) <= 170:
        return s
    if len(s) > 170:
        return trim_words(s, 165)
    additions = (
        " Check admission, fees, eligibility and placements.",
        " Get admission, fees, eligibility and placement details.",
        " Includes admission, fees, eligibility, cutoff and placements.",
    )
    for addition in additions:
        candidate = (s + addition).strip()
        if 120 <= len(candidate) <= 170:
            return candidate
    return trim_words((s or title) + " Check admission, fees, eligibility and placements.", 165)

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
for path in sorted(ROOT.glob("*.html")):
    if path.name in SKIP:
        continue
    raw = path.read_text(encoding="utf-8", errors="replace")
    if has_noindex(raw):
        continue

    title_match = re.search(r"<title\b[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
    if not title_match:
        continue

    old_title = clean(re.sub(r"<[^>]+>", " ", title_match.group(1)))
    new_title = TITLE_OVERRIDES[path.name] if path.name in TITLE_OVERRIDES else title_fix(old_title)
    updated = raw[:title_match.start()] + f"<title>{html.escape(new_title, quote=False)}</title>" + raw[title_match.end():]

    descriptions = [m for m in meta_tags(updated) if is_description(m.group(0))]
    old_description = attr(descriptions[0].group(0), "content") if descriptions else ""
    new_description = DESCRIPTION_OVERRIDES[path.name] if path.name in DESCRIPTION_OVERRIDES else description_fix(old_description, new_title)

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
        ("name", "twitter:card", "summary"),
        ("name", "twitter:title", new_title),
        ("name", "twitter:description", new_description),
    ]:
        updated = upsert_meta_content(updated, key, value, content)

    # Keep structured data synchronized with the final canonical, title and description.
    for schema_match in list(re.finditer(r'<script\b([^>]*)>(.*?)</script>', updated, flags=re.I | re.S)):
        attrs, body = schema_match.group(1), schema_match.group(2)
        if not re.search(r'type\s*=\s*["\']application/ld\+json["\']', attrs, flags=re.I):
            continue
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            continue
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
        replacement = f'<script{attrs}>{json.dumps(payload, ensure_ascii=False)}</script>'
        updated = updated[:schema_match.start()] + replacement + updated[schema_match.end():]

    if not re.search(r"<script\b[^>]*type\s*=\s*['\"]application/ld\+json['\"]", updated, flags=re.I):
        import json
        schema = json.dumps({"@context":"https://schema.org","@type":"WebPage","name":new_title,"description":new_description,"url":canonical}, ensure_ascii=False)
        updated = updated.replace("</head>", f'<script type="application/ld+json">{schema}</script>\n</head>', 1)

    if updated != raw:
        path.write_text(updated, encoding="utf-8")
        changed.append(path.name)

print(f"SEO metadata cleanup updated {len(changed)} pages")
