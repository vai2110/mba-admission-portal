from pathlib import Path
import re

MEASUREMENT_ID = "G-CPF48DTRTW"

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_PATHS = {
    "college-page-audit-dashboard.html",
    "content-audit.html",
    "github-direct-edit-test.html",
    "irma-deploy-trigger.html",
}

GOOGLE_TAG = f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{MEASUREMENT_ID}');
</script>"""

changed = 0
skipped = 0

for html_file in ROOT.rglob("*.html"):
    if any(part in {".git", "node_modules", ".github"} for part in html_file.parts):
        continue

    if html_file.name.lower() in EXCLUDED_PATHS:
        skipped += 1
        continue

    try:
        content = html_file.read_text(encoding="utf-8")
    except Exception:
        skipped += 1
        continue

    # Do not add Analytics to pages explicitly marked noindex.
    if re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
        content,
        re.IGNORECASE,
    ):
        skipped += 1
        continue

    # Prevent duplicate Google tags if a page is already configured.
    if (
        "googletagmanager.com/gtag/js" in content
        or re.search(r"gtag\\s*\\(\\s*['\"]config['\"]", content)
    ):
        skipped += 1
        continue

    head_match = re.search(r"<head\\b[^>]*>", content, re.IGNORECASE)
    if not head_match:
        skipped += 1
        continue

    insertion = "\n" + GOOGLE_TAG + "\n"
    updated = content[:head_match.end()] + insertion + content[head_match.end():]

    if updated != content:
        html_file.write_text(updated, encoding="utf-8")
        changed += 1

print(f"Google Analytics tag injected into {changed} HTML pages.")
print(f"Skipped {skipped} HTML pages.")
