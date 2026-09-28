#!/usr/bin/env bash
set -e
node scripts/normalize-clean-urls.js
python3 scripts/repair_internal_links_v2.py
python3 scripts/internal_link_audit.py
python3 scripts/seo_indexation_audit.py
python3 scripts/generate_sitemap.py
python3 scripts/final_seo_gate.py
node scripts/inject-guidance-flow.js
echo "SEO sitemap production sync trigger"
