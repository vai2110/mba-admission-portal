# CollegeDecoded URL Architecture Migration

## Status
- Phase: Inventory and architecture mapping
- Branch: `seo/url-architecture-migration`
- Base: `main`
- Production: **not modified**
- Scope: audit, route design, mapping, validation; production changes require review/PR

## Target hierarchy (approved reference)
- `/mba-colleges/` — college discovery hub
- `/mba-colleges/{college-slug}/` — college profile
  - `cutoff/`, `fees/`, `placements/`, `mba/`, `roi/`, `reviews/` only where distinct, substantial content and student intent justify indexable pages
- `/mba-colleges/city/{city-slug}/`
- `/mba-colleges/budget/{amount-slug}/`
- `/mba-colleges/exam/{exam-slug}/`
- `/mba-colleges/specialization/{spec-slug}/`
- `/exams/{exam-slug}/`, with `cutoff/` and `colleges-accepting/` child pages only where useful
- `/rankings/` with `nirf/`, `roi/`, `placements/`, `government/`
- `/tools/` with `predictor/`, `roi-calculator/`, `compare/`, `shortlist/`
- `/compare/{college-a}-vs-{college-b}/`
- `/guides/` with `admission-timeline/` and guide pages
- `/search?q=` remains utility-only, noindex, excluded from sitemap

## Migration principles
1. Inventory all URLs from sitemap, repository route generation, internal links, and Search Console exports where available.
2. Classify each URL by intent/type and record its index status, canonical, traffic/backlinks (if data is available), content uniqueness, and destination decision.
3. Map every old URL to one final canonical destination; decisions must be evidence-based.
4. Preserve valuable URLs when the SEO risk or content value of changing them outweighs hierarchy benefits. The proposed architecture is a target, not a mandate to rename every URL.
5. Never redirect unrelated or parameter-mismatched pages. Avoid redirect chains and loops.
6. Create child URLs only when content is distinct and genuinely useful; do not create thin section pages simply to satisfy the hierarchy.
7. All new routes must preserve the correct entity, page intent, metadata, canonical, breadcrumbs, and internal-link context.
8. Redirects, canonicals, sitemap, navigation, breadcrumbs, structured data, and internal links must be updated together.
9. Test in a Vercel preview and branch. **Do not push to `main`, merge, or deploy production as part of this audit.**
10. Monitor crawl/indexing changes after any approved rollout.

## Staged rollout
- Stage A: URL inventory and current-state crawl
- Stage B: proposed architecture and old-to-new mapping decisions
- Stage C: route implementation on this branch, starting with test/sample pages
- Stage D: redirect and canonical validation
- Stage E: internal-link and sitemap QA
- Stage F: Vercel preview QA (desktop/mobile, 200/301/404, canonical, content/entity matching)
- Stage G: review/PR; production only after explicit approval

## Go/no-go checks
- No redirect loops or chains
- Old URLs map to correct, relevant final destinations
- No 200 soft-404s or unintended 404s
- One canonical URL per page
- Sitemap contains canonical, indexable, 200 URLs only
- Internal links point directly to final URLs
- Correct college/exam entity and content match the URL
- Search/filter query URLs are not unintentionally indexable
- Mobile navigation and page content remain intact

## Known limitations at kickoff
The current public sitemap and robots endpoints could not be retrieved through the browsing connector in this session. The audit will therefore use repository route inventory, direct crawl methods where available, and sitemap/Search Console exports if necessary. The current route inventory must be verified before migration destinations are finalized.
