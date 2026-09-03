import os
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'index.html', '404.html', 'content-audit.html', 'college-page-audit-dashboard.html'}

# Frontend is locked to the existing IIM Ahmedabad content architecture +
# SIBM Pune visual system. This script does not invent a new design.
REQUIRED_CLASSES = {
    'hero': '.hero',
    'quick_answer': '.answer, .quick-answer, [class*="answer"]',
    'facts': '.facts, .fact, .facts-grid',
    'section': '.sec, .section, section',
}


def targets():
    raw = os.environ.get('TARGET_PAGES', '').strip()
    if raw:
        return [ROOT / x.strip() for x in raw.splitlines() if x.strip()]
    return []


def ensure_shared_css(soup):
    for link in soup.find_all('link', href=True):
        if 'college-page.css' in link.get('href', ''):
            return False
    head = soup.head
    if not head:
        raise RuntimeError('Missing <head>')
    tag = soup.new_tag('link', rel='stylesheet', href='college-page.css')
    head.append(tag)
    return True


def enforce(path):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    changed = False
    ensure_shared_css(soup)
    if not any('college-page.css' in (x.get('href') or '') for x in soup.find_all('link', href=True)):
        raise RuntimeError(f'{path.name}: shared college-page.css is missing')

    # Remove page-specific embedded CSS so every generated college page uses
    # the same locked frontend stylesheet rather than a model-created design.
    styles = soup.find_all('style')
    if styles:
        for style in styles:
            style.decompose()
        changed = True

    if not soup.select_one('.hero'):
        raise RuntimeError(f'{path.name}: locked .hero architecture missing')
    if not soup.select_one('.answer, .quick-answer, [class*="answer"]'):
        raise RuntimeError(f'{path.name}: locked Quick Answer architecture missing')
    if not soup.select_one('.facts, .fact, .facts-grid'):
        raise RuntimeError(f'{path.name}: locked facts architecture missing')
    if not soup.find('h1') or len(soup.find_all('h1')) != 1:
        raise RuntimeError(f'{path.name}: exactly one H1 is required')

    if changed:
        path.write_text(str(soup), encoding='utf-8')
    return path.name, changed


def main():
    results = []
    for path in targets():
        path = path.resolve()
        if path.parent != ROOT or path.suffix.lower() != '.html' or not path.exists() or path.name in EXCLUDED:
            continue
        results.append(enforce(path))
    print({'frontend_lock_checked': len(results), 'pages_changed': sum(x[1] for x in results), 'results': results})


if __name__ == '__main__':
    main()
