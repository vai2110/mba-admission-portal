import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "auto-fix-report.json"
EXCLUDED = {"index.html", "404.html", "content-audit.html"}

GENERIC_PATTERNS = [
    r"one of the (?:leading|premier|top|best|renowned|prestigious)", r"has carved a niche",
    r"stands as a (?:beacon|symbol)", r"plays a vital role", r"offers a wide range of",
    r"state[- ]of[- ]the[- ]art", r"world[- ]class", r"holistic (?:development|education|learning)",
    r"empowers students", r"nurtures (?:talent|leaders|students)", r"rich learning environment",
    r"vibrant campus life", r"dynamic learning environment", r"excellent career opportunities",
    r"bright career", r"strong foundation", r"in today's competitive", r"in the ever[- ]changing",
    r"aspiring (?:students|candidates) can",
]
PROMOTIONAL_PATTERNS = [
    r"best college", r"dream college", r"assured placement", r"100% placement",
    r"unmatched", r"unparalleled", r"number one", r"no\.\s*1",
]
NEGATED_PROMO_MARKERS = [
    "does not guarantee", "do not guarantee", "doesn't guarantee", "don't guarantee",
    "not guarantee", "not guaranteed", "cannot guarantee", "can't guarantee",
    "does not by itself guarantee", "does not automatically guarantee",
]


def normalized(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


def in_hero(node):
    if not node:
        return False
    hero_classes = {"hero", "hero-container", "hero-main", "hero-text"}
    for parent in [node, *node.parents]:
        classes = parent.get("class", []) if getattr(parent, "get", None) else []
        if any(cls in hero_classes for cls in classes):
            return True
    return False


def hero_hash(soup):
    hero = soup.select_one(".hero")
    if not hero:
        return None
    return hashlib.sha256(str(hero).encode("utf-8")).hexdigest()


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 35]


def is_negated(sentence):
    low = normalized(sentence)
    return any(marker in low for marker in NEGATED_PROMO_MARKERS)


def remove_matching_sentences(tag, patterns):
    text = tag.get_text(" ", strip=True)
    parts = sentences(text)
    if not parts:
        return False
    kept = []
    changed = False
    for sentence in parts:
        hit = any(re.search(pattern, sentence, flags=re.I) for pattern in patterns)
        if hit and not is_negated(sentence):
            changed = True
        else:
            kept.append(sentence)
    if not changed:
        return False
    if kept:
        if tag.name == "p":
            tag.clear()
            tag.append(" ".join(kept))
        else:
            return False
    else:
        tag.decompose()
    return True


def remove_duplicate_blocks(soup):
    seen = set()
    changed = 0
    for tag in list(soup.find_all(["p", "li"])):
        if in_hero(tag) or tag.find_parent(["script", "style", "nav", "header", "footer"]):
            continue
        text = normalized(tag.get_text(" ", strip=True))
        if len(text) < 45:
            continue
        if text in seen:
            tag.decompose()
            changed += 1
        else:
            seen.add(text)
    return changed


def fix_page(path):
    original = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(original, "html.parser")
    before_hero = hero_hash(soup)
    changes = []

    editable = [tag for tag in soup.find_all("p")
                if not in_hero(tag)
                and not tag.find_parent(["script", "style", "nav", "header", "footer"])]

    for tag in editable:
        if remove_matching_sentences(tag, GENERIC_PATTERNS):
            changes.append("removed generic/AI-style sentence")

    for tag in list(soup.find_all("p")):
        if in_hero(tag) or tag.find_parent(["script", "style", "nav", "header", "footer"]):
            continue
        if remove_matching_sentences(tag, PROMOTIONAL_PATTERNS):
            changes.append("removed promotional/absolute sentence")

    duplicate_count = remove_duplicate_blocks(soup)
    if duplicate_count:
        changes.append(f"removed {duplicate_count} exact duplicate content block(s)")

    after_hero = hero_hash(soup)
    if before_hero != after_hero:
        raise RuntimeError(f"Hero content changed unexpectedly in {path.name}; refusing to write page.")

    updated = str(soup)
    changed = updated != original
    if changed:
        path.write_text(updated, encoding="utf-8")

    return {"file": path.name, "changed": changed, "changes": changes, "hero_protected": True}


def main():
    target_pages = os.environ.get("TARGET_PAGES", "").strip()
    if target_pages:
        names = [x.strip() for x in target_pages.splitlines() if x.strip()]
        files = []
        for name in names:
            path = (ROOT / name).resolve()
            if path.parent != ROOT or path.suffix.lower() != ".html" or not path.exists() or path.name in EXCLUDED:
                continue
            files.append(path)
    else:
        files = [p for p in sorted(ROOT.glob("**/*.html")) if p.name not in EXCLUDED and ".git" not in p.parts]

    results = [fix_page(path) for path in files]
    changed = [r for r in results if r["changed"]]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "automatic-safe-editorial-fix",
        "pages_checked": len(results),
        "pages_changed": len(changed),
        "results": results,
        "limitations": [
            "Never changes hero content or hero HTML.",
            "Never invents, recalculates, or rewrites factual figures, fees, dates, cutoffs or placement statistics.",
            "Factual/source gaps remain in the audit report for review rather than being fabricated automatically.",
        ],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
