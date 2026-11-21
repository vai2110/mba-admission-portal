# URL Migration — Route Integration Constraints

**Reviewed:** 2026-11-21  
**Branch:** `seo/url-architecture-migration`  
**Scope:** Repository implementation audit only; no live crawl

## Verified configuration

`vercel.json` currently has:
- `cleanUrls: true`
- `trailingSlash: false`
- 75 explicit redirects and 28 rewrites
- Existing redirects mostly preserve established clean flat routes or map legacy aliases
- Existing rewrites include retired discovery URLs sent to the `/api/gone` handler; these must not be accidentally repurposed as new live route families

**Canonical convention:** use slashless non-root URLs to align with `trailingSlash: false`. The migration plan has been updated to reflect this.

## Route-normalization gap

`scripts/normalize-clean-urls.js` currently loops through only root-level HTML files using `fs.readdirSync(ROOT)` and skips nested HTML files. Its canonical helper derives a clean URL from a filename (and treats only root `index.html` as the homepage). This is appropriate for the existing flat route set but is not hierarchy-aware for the proposed nested routes.

The internal-link normalization and local-target existence checks have some nested-path support, but they do not make the file-processing loop or canonical generation hierarchy-aware.

**Implementation requirement:** before moving pages, update the normalization/canonical logic to support nested files and directory index routes explicitly, while preserving existing root-level behavior and CMS overview exceptions. Add tests for root pages, nested `*.html`, nested `index.html`, query/hash preservation, aliases, retired routes and CMS profiles.

## Sitemap and route validation

- `scripts/generate_sitemap.py` recursively scans HTML and uses declared canonicals when present. This is a good foundation for hierarchical routes.
- Its fallback logic treats an `index.html` as the site homepage when a canonical is absent; nested directory index files must therefore have an explicit correct canonical or the sitemap can misidentify them.
- `scripts/validate_sitemap_routes.py` resolves normal nested routes to either `path.html` or `path/index.html`. It does not currently resolve CMS `college-cms/content/{slug}/overview.html` as a public route by slug.
- `scripts/final_seo_gate.py` already computes canonical expectations for nested directory-index routes and CMS overview files, so it can serve as a regression check but should be tested against the migration's exact route rules.

**Implementation requirement:** test sitemap generation and validation against profile, MBA, placements, exam and hub examples, including nested directory-index files and CMS sources. Sitemap must contain only one slashless canonical URL per indexable route.

## Internal-link audit scope gap

`scripts/internal_link_audit.py` scans root-level HTML files via `ROOT.glob("*.html")`. Its link resolution can recognize nested targets, but the source-page scan and cluster/orphan analysis are root-only.

**Implementation requirement:** extend the audit to scan recursive public HTML sources, with explicit exclusions for CMS source files, tests, internal tools and noindex pages. Avoid treating a CMS storage path as a public route. Report internal links that resolve through redirects and any new-route orphan/cluster gaps.

## Build pipeline and existing guardrails

`scripts/vercel-build.sh` runs the URL normalizer and data consistency checks, generates the sitemap, then executes route/sitemap, internal-link, SEO and structured-data validators, followed by final gates. A route migration must not bypass these checks or reorder generators in a way that produces stale canonicals or links.

Existing gates should remain mandatory; add hierarchy-specific checks where needed:
- canonical count and expected canonical path
- source file exists for every indexable route
- sitemap URL resolves to a route and is canonical
- internal links resolve directly to final routes (no redirecting links)
- no redirect loops, chains or cross-entity destinations
- no accidental noindex pages in sitemap
- profile/programme/placement entity consistency
- slash convention is consistent

## Recommended implementation order

1. Finish and approve content-grounded old-to-new mapping decisions; do not treat metadata samples as final migration approval.
2. Establish slashless canonical route policy (now reflected in the migration plan).
3. Make normalization and canonical generation nested-route aware; add regression tests before mass file moves.
4. Extend sitemap route resolution and internal-link audit to cover public nested pages and CMS mappings.
5. Implement a small representative route cluster on this branch only (one profile, distinct MBA, placements, plus one hub/exam).
6. Validate build gates, redirect behavior, content/entity matching, canonicals and Vercel preview desktop/mobile.
7. Only after full review create a PR. Production merge/deployment requires explicit user approval.

## Current decision and risk

- No hierarchical route files, route rewrites or migration redirects were implemented in this review.
- The existing flat URL architecture and normalization pipeline are not yet ready for a mass route move without the above integration changes.
- This is a repository-based assessment; live HTTP status, live canonical output, redirect chains and Vercel rendering remain unverified.
