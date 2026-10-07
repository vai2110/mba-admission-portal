#!/usr/bin/env bash
set -e
python3 scripts/seo_metadata_cleanup.py
node scripts/normalize-clean-urls.js
node scripts/validate-college-data-consistency.js
python3 scripts/repair_internal_links_v2.py
python3 scripts/repair_orphan_links.py
python3 scripts/internal_link_audit.py
python3 - <<'PY'
import json
from pathlib import Path
report = json.loads(Path("internal-link-audit.json").read_text(encoding="utf-8"))
summary = report["summary"]
print(f"INTERNAL LINK GATE: {summary['cluster_reciprocal_gaps']} reciprocal gaps; {summary['broken_local_links']} broken local links; {summary.get('redirecting_internal_links', 0)} redirecting internal links.")
if summary["broken_local_links"] or summary["cluster_reciprocal_gaps"] or summary.get("redirecting_internal_links", 0):
    raise SystemExit("INTERNAL LINK GATE FAILED")
print("INTERNAL LINK GATE PASSED")
PY
python3 scripts/seo_indexation_audit.py
python3 scripts/generate_sitemap.py
python3 scripts/final_seo_gate.py
node scripts/inject-guidance-flow.js
echo "SEO sitemap production sync trigger"
