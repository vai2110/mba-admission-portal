#!/usr/bin/env python3
"""Fail the production build if SEO-Geo JSON-LD is malformed or embedded in CSS."""
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parents[1]
MARKER='<script data-mba-schema="seo-geo-aeo"'
def main():
    errors=[]; checked=0
    for path in sorted(ROOT.rglob("*.html")):
        if any(x in {".git","node_modules",".vercel"} for x in path.parts): continue
        raw=path.read_text(encoding="utf-8",errors="ignore"); lower=raw.lower()
        if "</s<script data-mba-schema" in lower: errors.append(f"{path.relative_to(ROOT)}: split style/schema tag")
        for m in re.finditer(re.escape(MARKER),lower):
            checked+=1; pos=m.start()
            if lower.rfind("<style",0,pos)>lower.rfind("</style>",0,pos):
                errors.append(f"{path.relative_to(ROOT)}: schema is inside an unclosed style block")
            gt=raw.find(">",pos); end=lower.find("</script>",gt+1 if gt>=0 else pos)
            if gt<0 or end<0: errors.append(f"{path.relative_to(ROOT)}: schema script is not closed"); continue
            try: json.loads(raw[gt+1:end].strip())
            except Exception as e: errors.append(f"{path.relative_to(ROOT)}: invalid schema JSON ({e})")
    if errors:
        print("HTML STRUCTURE VALIDATION FAILED:\n"+"\n".join(" - "+e for e in errors[:100])); raise SystemExit(1)
    print(f"HTML STRUCTURE VALIDATION PASSED: {checked} SEO-Geo JSON-LD blocks valid.")
if __name__=="__main__": main()
