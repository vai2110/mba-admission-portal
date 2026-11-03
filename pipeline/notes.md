# Repository inspection notes

Inspection date: 2026-11-03

## Repository and deployment
- Repository: `vai2110/mba-admission-portal`
- Default branch: `main`
- Working branch: `seo/indexing-fixes` (created from `main`)
- Vercel project: `mba-admission-portal`
- Production domain: `collegedecoded.in`
- Vercel reports `framework: null`; the latest existing deployment inspected was a READY preview built from `fix/top-mba-colleges-ranking-page`, not this new branch.

## Framework and page generation
- The site is a static HTML site hosted on Vercel, not a Next.js or Astro app.
- Root repository inspection found 772 entries, including 667 root-level HTML files, plus `api/`, `assets/`, `college-cms/`, `config/`, `data/`, `iim-ahmedabad/`, `integrations/`, `news/`, and `scripts/`.
- There is no root `package.json`. Vercel runs `bash scripts/vercel-build.sh` and publishes the repository root.
- `scripts/normalize-clean-urls.js` normalizes internal links and writes canonical tags. Its current behavior derives canonicals from the source filename, so it needs special handling for duplicate consolidation.
- `scripts/generate_college_guides_hub.py` generates the crawlable college directory.
- `scripts/generate_sitemap.py` generates the XML sitemap and derives lastmod from Git history, with filesystem mtime fallback.
- `scripts/seo_metadata_cleanup.py` applies metadata overrides and cleanup.
- `vercel.json` contains cleanUrls/trailingSlash settings, rewrites and permanent redirects.
- `robots.txt` currently allows all user agents and references both the main sitemap and news sitemap.

## Existing baseline evidence (historical, not live verification)
- `technical-seo-audit.json`: 668 pages checked, 46 pages with issues. The stored report lists 40 H1-count issues, 2 JSON-LD issues, 2 noindex issues, 2 OG metadata groups, and other metadata/viewport issues.
- `internal-link-audit.json`: 664 pages checked, 49 zero-incoming pages, 85 college clusters, 31 reciprocal-link gaps. Stored report date: 2026-10-13.
- `sitemap.xml`: 668 URLs in the inspected revision. Stored lastmod values were 2026-10-17 and 2026-10-30.
- `content-audit-report.json` includes some page-level word counts, but is not a complete inventory of all pages.
- Existing audit outputs are stale snapshots and must be regenerated on the PR preview before being treated as current.

## Mobile architecture
- Mobile rules are distributed across per-college CSS files and inline page styles. Several page families have responsive breakpoints, but there is no single shared responsive layer applied consistently across all HTML pages.
- `scripts/ux_mobile_audit.py` exists and checks viewport tags, responsive CSS, table overflow wrappers, image alt text, horizontal-overflow risk and mobile navigation. It has not yet been run against the current branch preview.
- Mobile changes must be additive and scoped to small screens. Desktop structure, branding, information architecture and component styling must remain unchanged.

## Initial risks to address
1. Duplicate pages may be independently self-canonical because the normalizer rewrites canonicals from filenames.
2. The sitemap is generated from static files and canonicals but does not itself prove a route returns HTTP 200.
3. Historical internal-link data shows orphan candidates that need a fresh crawl and link repair.
4. Per-page CSS duplication creates inconsistent mobile behavior.
5. Some titles contain ellipses, as shown by the stored technical audit and the Chitkara page inspected.

No production files, environment variables, secrets, billing, domain or DNS settings were changed during this inspection.
