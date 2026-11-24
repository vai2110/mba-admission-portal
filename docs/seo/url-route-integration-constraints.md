# URL Migration — Route Integration Constraints

**Reviewed:** 2026-11-24  
**Branch:** `seo/url-architecture-migration`  
**Scope:** Repository implementation audit only; live crawl and Search Console verification remain separate.

## Verified configuration

`vercel.json` currently has:
- `cleanUrls: true`
- `trailingSlash: false`
- 75 explicit redirects and 28 rewrites
- Existing redirects mostly preserve established clean flat routes or map legacy aliases
- Existing rewrites include retired discovery URLs sent to the `/api/gone` handler; these must not be repurposed accidentally

**Canonical convention:** use slashless non-root URLs to align with `trailingSlash: false`; homepage canonical remains `https://collegedecoded.in/`.

## URL normalization and public-route collection

The nested-route support is **partially implemented**, not root-only:

- `scripts/collect-public-html-for-normalization.js` collects root-level HTML plus recursive HTML under the explicit allowlist `mba-colleges`. It excludes hidden directories, symlinks, `.git`, `.vercel`, `node_modules`, and `college-cms`.
- `scripts/normalize-clean-urls.js` uses that collector, normalizes internal links, and writes canonicals from the source HTML path. It only normalizes nested public pages under the allowlisted `mba-colleges` root; unrelated nested legacy folders remain outside the normalization scope.
- `scripts/public-route-from-html-path.js` supports root HTML, nested regular HTML, root `index.html`, and nested directory-index files. Nested `index.html` maps to its directory route, e.g. `mba-colleges/iim-ahmedabad/fees/index.html` → `/mba-colleges/iim-ahmedabad/fees`.
- Nested public pages should use root-relative internal hrefs. Browser-relative links from slashless directory-index URLs can resolve to a different path than the filesystem sibling the author intended.
- CMS overview files stored at `college-cms/content/{slug}/overview.html` are handled as public profile routes at `/{slug}` only when the profile is published.

**Implementation requirement:** keep the allowlist explicit and safe. Before expanding nested route families, add regression tests for root and nested files, directory-index routes, relative and root-relative links, query/hash suffixes, aliases, retired routes, CMS published/unpublished profiles, hidden folders and symlink boundaries.

## Sitemap generation and validation

- `scripts/generate_sitemap.py` recursively scans HTML and uses page canonicals when declared. It filters to clean canonical URLs on the CollegeDecoded origin and excludes noindex pages and legacy `.html` URLs.
- Nested `index.html` sources publish at directory routes. They must have explicit correct canonicals; without one, fallback route handling can misidentify a nested index.
- `scripts/validate_sitemap_routes.py` resolves clean URLs to `path.html` or `path/index.html`, checks canonical count and exact match, and rejects noindex pages listed in the sitemap. It does not map CMS storage path `college-cms/content/{slug}/overview.html` to the public `/{slug}` route by slug.
- `scripts/final_seo_gate.py` recursively checks HTML and computes expected canonical routes for nested directory-index files and CMS overview storage paths.

**Implementation requirement:** validate profile, programme, placement, exam and hub examples, including nested directory-index routes and CMS source-to-public mapping. Sitemap entries must be unique, slashless canonical, indexable, and resolve to the correct page entity.

## Internal-link audit scope

`scripts/internal_link_audit.py` scans root-level HTML and nested public pages under the allowlisted `mba-colleges` tree. It excludes hidden directories, symlinks and internal/CMS/generated directories such as `.git`, `.vercel`, `node_modules`, `college-cms`, `tests` and `scripts`. Local-link resolution supports nested `.html` and directory-index routes and flags missing local targets.

**Known limitation:** the audit's cluster reciprocity and zero-incoming/orphan analysis remain root-level focused, even though nested pages are included in link-resolution checks. Do not treat nested cluster/orphan coverage as complete.

**Implementation requirement:** expand cluster/orphan analysis to nested public routes with explicit route-family/entity rules, and report links that resolve through redirects, broken links, reciprocal-link gaps and new-route orphan candidates.

## Build pipeline and existing guardrails

`scripts/vercel-build.sh` runs URL normalization and data-consistency checks, repairs orphan links, generates the base sitemap, then runs sitemap validation, internal-link and SEO/structured-data checks and the remaining gates. Migration work must not bypass these checks or change their order without verifying that canonicals and links are generated from the final routes.

Keep/add tests for:
- exactly one canonical and the expected canonical path for each indexable route
- source file exists for every indexable route
- sitemap URL resolves to the intended route and canonical
- internal links resolve directly to final routes (not redirecting links)
- no redirect loops, chains or cross-entity destinations
- no accidental noindex pages in sitemap
- profile/programme/placement entity consistency
- slash convention consistency
- nested cluster reciprocity and orphan detection once that analysis is expanded

## Recommended implementation order

1. Complete content-grounded old-to-new mapping decisions; metadata samples are not final approval.
2. Keep the slashless canonical convention consistent across internal links, redirects, canonicals and sitemap.
3. Expand the route-normalizer allowlist only after tests cover the intended route families and CMS exceptions.
4. Extend nested sitemap/CMS route validation and cluster/orphan analysis.
5. Convert a small representative content cluster on this branch only.
6. Verify redirect behavior, content/entity match, canonicals, internal links, sitemap, build gates and Vercel preview desktop/mobile.
7. Open/review PR only after evidence-based mapping and QA. Production merge/deployment requires explicit user approval.

## Current decision and risk

- The four IIM Ahmedabad nested preview routes are committed on this branch, but preview deployment status alone is not full route-level QA.
- Four legacy programme links on the IIMA fees page still point to existing flat URLs; keep them until destination pages are content-verified and converted. Do not replace them with unbuilt nested URLs.
- The master mapping ledger has 35 rows, 34 proposed destinations, 33 `MIGRATE CANDIDATE`, 1 `REVIEW`, 1 `KEEP/REVIEW`, and zero approved redirect targets. Live status, Search Console, internal-link and final redirect decisions remain pending.
- Repository inventory and sitemap counts (684 HTML entries vs 668 sitemap entries in the recorded inventory) still require reconciliation.

This document describes the current repository implementation; it does not certify live HTTP responses, redirect chains, current indexability or Search Console outcomes.
