from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"404.html", "iim-ahmedabad.html", "sibm-pune.html"}

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def trim_words(s, n):
    s = clean(s)
    if len(s) <= n:
        return s
    x = s[: n + 1]
    if " " in x:
        x = x[: x.rfind(" ")]
    return x.rstrip(" ,:;-|&") + "…"

def title_fix(s):
    s = clean(s)
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
    s = clean(s)
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
    new_title = title_fix(old_title)
    updated = raw[:title_match.start()] + f"<title>{new_title}</title>" + raw[title_match.end():]

    descriptions = [m for m in meta_tags(updated) if is_description(m.group(0))]
    old_description = attr(descriptions[0].group(0), "content") if descriptions else ""
    new_description = description_fix(old_description, new_title)

    if descriptions:
        first = descriptions[0]
        new_tag = set_attr(first.group(0), "content", new_description.replace('"', "&quot;"))
        updated = updated[:first.start()] + new_tag + updated[first.end():]
        descriptions = [m for m in meta_tags(updated) if is_description(m.group(0))]
        for match in reversed(descriptions[1:]):
            updated = updated[:match.start()] + updated[match.end():]
    else:
        updated = updated.replace("</title>", f'</title>\n<meta name="description" content="{new_description.replace(chr(34), "&quot;")}">', 1)

    if updated != raw:
        path.write_text(updated, encoding="utf-8")
        changed.append(path.name)

print(f"SEO metadata cleanup updated {len(changed)} pages")
