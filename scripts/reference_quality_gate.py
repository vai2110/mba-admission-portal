"""Deterministic reference-architecture QA for the independent college agent.

Standalone: does not read, import, execute or follow AGENTS.md or any other
repository agent configuration. It validates generated HTML against the
approved college-page.css component architecture and supplies a generation
contract for Gemini.
"""
import re
from bs4 import BeautifulSoup

VERSION = "1.1"


def _has_class(soup, pattern):
    rx = re.compile(pattern, re.I)
    return bool(soup.find(class_=rx) or soup.find(id=rx))


def _internal_links(soup):
    links = []
    for a in soup.find_all("a", href=True):
        href = str(a.get("href", "")).strip()
        if href and not href.startswith(("http://", "https://", "#", "mailto:", "tel:", "javascript:")):
            links.append(href.split("#")[0].split("?")[0].lstrip("/"))
    return [x for x in links if x]


def _faq_questions(soup):
    items = soup.find_all(class_=re.compile(r"faq-item", re.I))
    count = 0
    for item in items:
        if item.find(["h3", "h4", "h5"]):
            count += 1
    return count


def validate_reference_architecture(html, page_type=""):
    """Return (penalty, critical_failures, notes, checks)."""
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    critical = []
    notes = []
    checks = {}
    penalty = 0

    def required(name, ok, message, weight=4):
        checks[name] = bool(ok)
        if not ok:
            critical.append("reference architecture: " + message)
            nonlocal penalty
            penalty += weight

    required("html5", bool(re.search(r"<!doctype\s+html", html or "", re.I)), "missing HTML5 doctype")
    required("header", bool(soup.find("header")), "site header missing")
    required("nav", bool(soup.find("nav")), "primary navigation missing")
    required("hero", _has_class(soup, r"^hero$|college[-_ ]hero"), "hero section missing")
    required("quick_facts", _has_class(soup, r"quick[-_ ]facts?"), "quick-facts strip missing")
    required("quick_fact_items", len(soup.find_all(class_=re.compile(r"quick[-_ ]fact$", re.I))) >= 3, "fewer than 3 quick-fact cards")
    required("page_layout", _has_class(soup, r"^page[-_ ]layout$"), "reference page-layout container missing")
    required("desktop_on_page", _has_class(soup, r"^sidebar$|^sidebar[-_ ]card$|on[-_ ]this[-_ ]page|table[-_ ]of[-_ ]contents|^toc$"), "desktop On This Page/sidebar navigation missing")
    required("mobile_on_page", _has_class(soup, r"^mobile[-_ ]on[-_ ]page$|mobile[-_ ]section[-_ ]nav"), "mobile On This Page navigation missing")
    required("content_container", _has_class(soup, r"^content$"), "main content container missing")
    required("main_sections", len(soup.find_all(class_=re.compile(r"^main[-_ ]section$", re.I))) >= 5, "fewer than 5 reference main-section cards")
    required("h1", len(soup.find_all("h1")) == 1, "page must contain exactly one H1")
    required("h2", len(soup.find_all("h2")) >= 5, "fewer than 5 useful H2 sections")
    required("cards", bool(soup.find(class_=re.compile(r"programme[-_ ]card|highlight|pro[-_ ]box|warning[-_ ]box|official[-_ ]link|card|grid", re.I))), "card/grid component structure missing")
    required("table", bool(soup.find("table")), "at least one useful factual table is required")
    required("answer_box", bool(soup.find(class_=re.compile(r"^answer[-_ ]box$", re.I))), "answer-first answer box missing")
    required("cta", bool(soup.find(class_=re.compile(r"^cta$|call[-_ ]to[-_ ]action", re.I))) or bool(soup.find("a", href=re.compile(r"apply|admission|contact", re.I))), "student CTA missing")
    required("faq", bool(soup.find(class_=re.compile(r"^faq|faq[-_ ]section", re.I))), "FAQ component missing")
    required("faq_questions", _faq_questions(soup) >= 3, "fewer than 3 structured FAQ questions")
    required("sources", _has_class(soup, r"official[-_ ]links?|official[-_ ]sources?|^sources$|^references$"), "official source/reference section missing")
    required("source_links", len(soup.find_all(class_=re.compile(r"official[-_ ]link", re.I))) >= 1, "official source links/cards missing")
    required("internal_links", len(_internal_links(soup)) >= 2, "fewer than 2 internal links")
    required("viewport", bool(soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})), "viewport meta missing")
    required("stylesheet", bool(soup.find("link", href=re.compile(r"college-page\.css", re.I))) or "college-page.css" in (html or ""), "shared college-page.css missing")
    required("title", bool(soup.title and soup.title.get_text(strip=True)), "title tag missing")
    required("description", bool(soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})), "meta description missing")
    required("canonical", bool(soup.find("link", rel=re.compile(r"canonical", re.I))), "canonical URL missing")
    required("og", bool(soup.find("meta", attrs={"property": re.compile(r"^og:title$", re.I)})) and bool(soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})), "complete OG title/description missing")
    required("json_ld", bool(soup.find("script", attrs={"type": re.compile(r"application/ld\+json", re.I)})), "JSON-LD structured data missing")

    required_terms = {
        "programme": {
            "admission": r"\badmission\b",
            "eligibility": r"\beligib(?:ility|le)\b",
            "fees": r"\bfees?\b|\btuition\b",
            "selection": r"\bselection\b",
            "curriculum": r"\bcurriculum\b|\bprogramme structure\b|\bprogram structure\b",
        },
        "placement": {
            "placement": r"\bplacement\b",
            "career": r"\bcareer\b|\brecruit",
        },
        "overview": {
            "overview": r"\boverview\b|\babout\b",
            "admission": r"\badmission\b",
            "programme": r"\bprogramme\b|\bprogram\b",
            "placement": r"\bplacement\b|\bcareer\b",
        },
    }.get(page_type, {})
    for key, pattern in required_terms.items():
        ok = bool(re.search(pattern, text, re.I))
        required(f"{page_type}_{key}", ok, f"{page_type} page missing {key} content", 3)

    if len(text) < 1800:
        notes.append("reference architecture: content depth below 1,800 visible characters; expand with verified student-useful information")
        penalty += 3
    if len(text) < 1000:
        critical.append("content quality: page is too thin for production")
        penalty += 6
    if re.search(r"lorem ipsum|placeholder|insert here", text, re.I):
        critical.append("content quality: placeholder text detected")
        penalty += 10

    empty_sections = 0
    for section in soup.find_all(class_=re.compile(r"main[-_ ]section", re.I)):
        if len(section.get_text(" ", strip=True)) < 120:
            empty_sections += 1
    if empty_sections:
        critical.append(f"reference architecture: {empty_sections} main-section component(s) are effectively empty")
        penalty += min(12, empty_sections * 4)

    return min(penalty, 70), critical, notes, checks


REFERENCE_PROMPT = """
REFERENCE ARCHITECTURE CONTRACT — NON-NEGOTIABLE

Generate a production-ready college page using the approved `college-page.css` architecture. Do not return a plain document of headings and paragraphs. The page must visually follow the established reference pattern: sticky header/navigation, hero, quick facts, desktop On This Page sidebar, mobile On This Page control, white content cards, factual tables, answer boxes, grids/cards, FAQ, official sources and related/internal links.

Use these exact shared component classes from college-page.css wherever applicable:
- `header` + `.navbar` + `.nav-links`
- `.hero`
- `.quick-facts` containing at least 3 `.quick-fact` cards
- `.page-layout` with `.sidebar`/`.sidebar-card` and `.content`
- `.mobile-on-page`
- at least 5 `.main-section` cards
- `.answer-box`
- `.table-wrapper` around factual tables
- `.programme-grid`, `.highlight-grid`, `.two-column`, `.programme-card`, `.highlight`, `.pro-box`, or `.warning-box` where useful
- `.cta` for the main student action
- `.faq-item` inside a clearly identified FAQ section
- `.official-links` with `.official-link` cards

Every generated page MUST have:
1. Complete HTML5 document and viewport meta.
2. One H1 and at least 5 meaningful H2 sections, with H3s where useful.
3. Hero + quick facts + desktop On This Page + mobile On This Page.
4. At least 5 substantial `.main-section` cards; never add empty/placeholder sections.
5. At least one useful table for factual information when applicable.
6. At least one answer box and one clear `.cta`.
7. At least 3 structured `.faq-item` questions with college-specific, source-grounded answers.
8. Official Sources section with actual supplied official URLs.
9. At least 2 valid internal links to known existing/package files. Never invent a URL.
10. Title, meta description, canonical, OG title/description and valid JSON-LD.
11. Link `college-page.css`; keep markup responsive and mobile-first.
12. Answer-first, student-centric, simple English. No generic AI intro, keyword stuffing, repetition or unsupported marketing language.
13. Use only supplied official research for facts. If a fact is not published, explicitly say it is not published by the official source. Never fabricate fees, dates, cutoffs, seats, salaries, recruiters or statistics.

The architecture is a hard QA gate. A page that does not satisfy it must not be considered publishable even if its prose or SEO score is otherwise high.
""".strip()


def append_reference_contract(prompt):
    return str(prompt) + "\n\n" + REFERENCE_PROMPT
