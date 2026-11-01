# CollegeDecoded SEO and URL Governance — Phase 0/1 Handover

Baseline inspected: commit f4f51c78a36a121910fe67fe68328688e6c3867c on main.

## Scope and safety

This change adds read-only URL inventory tooling and routes automated site writers through pull-request review. It does not publish to production, delete content, change canonical URLs, merge page intents, apply noindex, or create permanent redirects.

The IIM Ahmedabad hierarchy below is a proposed target, not an applied migration. Existing page content and URL equity must be preserved until the Google Search Console page/query export (last 16 months) has been reviewed and candidate pages compared for clicks, impressions, CTR, average position, backlinks and distinct intent.

## Repository baseline

- Static HTML site; Vercel build output is the repository root.
- Sitemap contains 668 URLs at the inspected commit.
- Repository contains 666 root-level HTML files and 16 CMS overview HTML files (682 HTML files total).
- vercel.json contains 68 explicit redirects and 28 rewrites.
- Overlapping data sources include college-content-master.csv (100 rows), college-content-priority.csv (100 rows), college-content-overrides.csv (one data row), college-production-state.json (100 rank-keyed records), and management-live-colleges.json (102 records). These do not yet share one enforced identity/URL key.
- technical-seo-audit.json and internal-link-audit.json are stale snapshots. The technical report references eight HTML files absent from the current tree. Do not use its historical issue count as a current live issue count.
- generate_sitemap.py derives lastmod from Git commit timestamps with filesystem modification-time fallback. The current sitemap dates are concentrated on 2026-10-17 and 2026-10-30; these are not independently verified content-change dates.

## Confirmed route/content conflicts

Five CMS overview files are shadowed by Vercel redirects:

| CMS slug | CMS file | Configured destination | Risk |
|---|---|---|---|
| iiswbm-kolkata | college-cms/content/iiswbm-kolkata/overview.html | /mba-colleges-in-kolkata (configured to return 410) | Individual college content is shadowed by a retired hub |
| globsyn-business-school-kolkata | college-cms/content/globsyn-business-school-kolkata/overview.html | /mba-colleges-in-kolkata (410) | Same |
| edii-ahmedabad | college-cms/content/edii-ahmedabad/overview.html | /mba-colleges-in-ahmedabad (410) | Individual college content is shadowed by a retired hub |
| mnit-jaipur-mba | college-cms/content/mnit-jaipur-mba/overview.html | /mba-colleges-by-location | College-specific route resolves to a generic hub |
| jaipuria-jaipur-mba | college-cms/content/jaipuria-jaipur-mba/overview.html | /mba-colleges-by-location | Campus-specific route resolves to a generic hub |

These routes are not automatically restored. Confirm college/campus identity, content freshness and GSC demand before changing them.

## IIM Ahmedabad pilot — proposed structure only

| Page intent | Proposed URL | Existing candidates |
|---|---|---|
| College trunk | /iim-ahmedabad | iim-ahmedabad.html |
| Placements | /iim-ahmedabad/placements | iim-ahmedabad-placements.html |
| PGP | /iim-ahmedabad/programmes/pgp | iim-ahmedabad-mba.html, iim-ahmedabad-mba-pgp.html |
| PGPX | /iim-ahmedabad/programmes/pgpx | iim-ahmedabad-pgpx.html, iim-ahmedabad-mba-pgpx.html |
| FABM | /iim-ahmedabad/programmes/fabm | iim-ahmedabad-mba-fabm.html |
| BPGP | /iim-ahmedabad/programmes/bpgp | iim-ahmedabad-mba-bpgp.html, iim-ahmedabad-business-analytics-ai.html |

These pairs are consolidation candidates, not confirmed duplicates. Preserve unique content and separate admission cycles until the full pages and GSC data have been compared. Keep admission, fees and cutoff as anchors initially unless distinct, substantial intent justifies a separate page.

### IIMA content consistency findings

- The trunk page H1 says Admission 2027 while its title says Admission 2026.
- The legacy iim-ahmedabad-mba page mixes PGP 2027–29 heading language with 2026–28/CAT 2025 references.
- The iim-ahmedabad-mba-pgp page describes the 2027–29 cycle and CAT 2026.
- The placements page mixes placement-cycle labels and audited report-year language. Historical 2025 figures must remain labelled historical; do not silently replace them with 2026 figures.

## Automation safety changes

Five workflows previously contained direct git push origin HEAD:main operations:

- technical-seo-audit.yml
- content-audit.yml
- generate-sitemap.yml
- apply-homepage-v2.yml
- college-existing-page-audit.yml

This PR routes their generated site changes through pull requests. The existing-college audit must not mark a page as deployed/live before its proposed HTML is merged and verified on the actual production host.

## Evidence needed before destructive URL decisions

1. Google Search Console exports for the last 16 months: Pages and Queries, including clicks, impressions, CTR and average position for the candidate college URLs.
2. Backlink/referring-domain data if available.
3. Confirm whether the five shadowed CMS profiles should be active individual college profiles. Safe default: preserve files and defer route changes pending identity/content review.
4. Production HTTP crawl after the inventory workflow: status, final URL, canonical response, robots directives and indexability. Repository files alone cannot prove live Vercel responses.
5. Review and approve the IIMA pilot mapping after page-content comparison and GSC analysis.

## Rollout gates

- Generate and inspect the URL inventory artifact from the workflow in this PR.
- Fix confirmed missing/mismatched canonicals, orphan links and route shadowing in small PRs, with live checks.
- Reconcile current CSV/JSON registries before introducing a single college/programme identity registry.
- Apply the IIMA hierarchy only after the GSC and content-comparison gate.
- Roll out other colleges in batches; do not bulk-rewrite URLs or programme pages without evidence.
