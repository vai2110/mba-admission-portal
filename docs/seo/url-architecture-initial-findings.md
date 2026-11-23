# URL Architecture Audit — Initial Repository Findings

**Audit date:** 2026-11-21  
**Repository audited:** `vai2110/mba-admission-portal` (`main`)  
**Working branch:** `seo/url-architecture-migration`  
**Production status:** No production or main-branch changes

## Evidence reviewed
- Repository recursive Git tree (non-truncated; 1,007 tracked tree entries)
- `sitemap.xml`
- `scripts/normalize-clean-urls.js`
- `.github/workflows/migrate-clean-urls.yml`
- `index.html`
- `AGENTS.md` site/content constraints

## Initial findings

1. **Flat URL architecture dominates.** The repository has 684 HTML files: 667 root-level HTML files and 17 nested HTML files. Most nested files are CMS source paths, not clearly exposed public URLs; the only other nested HTML path observed was `iim-ahmedabad/courses-fees/index.html`. This is repository-level evidence, not a live crawl.
2. **Current public URLs use mostly clean flat slugs.** The sitemap lists clean routes such as `/iim-ahmedabad`, `/amity-university-noida`, `/amity-university-noida-mba`, `/amity-university-noida-placements`. This differs materially from the proposed `/mba-colleges/{college-slug}/` parent-child structure.
3. **The current clean-URL system is already implemented.** `scripts/normalize-clean-urls.js` normalizes internal anchors, removes `.html`, resolves relative paths, checks local target existence, applies route aliases, and writes a canonical based on the clean root-level route. A new hierarchy must integrate with this logic rather than replace it blindly.
4. **A previous migration workflow exists.** `.github/workflows/migrate-clean-urls.yml` is documented as a one-time clean-URL migration workflow and installs legacy redirects. It is manual-triggered. This suggests the current clean flat URL system has migration history and should be treated carefully.
5. **Sitemap concerns to validate.** The repository's `sitemap.xml` shows `lastmod=2026-10-17` repeated in entries. Freshness and correctness should be audited; do not bulk-update `lastmod` without evidence of actual page modification.
6. **CMS source paths are not necessarily public routes.** The 16 `college-cms/content/{slug}/overview.html` files are storage/source paths and must be mapped to their clean canonical public URLs before they are included in public route inventory.
7. **The requested hierarchy is not just URL renaming.** The target adds meaningful college profile children (fees, placements, cutoff, ROI, reviews, programmes), exam hubs, ranking hubs, tools, comparison pages and guides. Each indexable child requires distinct useful content and valid links; thin section clones must not be created.

## Initial architecture comparison

| Area | Current repository pattern | Target pattern | Initial status |
|---|---|---|---|
| College profiles | Root-level `/{college-slug}` | `/mba-colleges/{college-slug}/` | Major migration |
| Programme pages | Root-level `/{college-slug}-{programme}` | College/programme hierarchy | Major mapping required |
| Fees pages | Root-level `/{college-slug}-fees` or variants | College child `/fees/` + budget hub | Major mapping required |
| Placement pages | Root-level `/{college-slug}-placements` | College child `/placements/` + ranking hub | Major mapping required |
| Cutoffs | Mostly root-level or broad pages | College child and exam cutoff routes | Major mapping required |
| City hubs | Existing root-level city/discovery slugs | `/mba-colleges/city/{city}/` | Map and consolidate |
| Exam pages | Root-level `/cat`, `/xat`, etc. | `/exams/{exam-slug}/` | Major migration |
| Ranking hubs | Mixed root-level topic pages | `/rankings/{type}/` | Inventory needed |
| Tools | Mixed/standalone routes | `/tools/{tool}/` | Inventory needed |
| Comparison | Existing comparison files/data | `/compare/{a}-vs-{b}/` | Inventory needed |
| Guides | Root-level and guide hub files | `/guides/{guide-slug}/` | Inventory needed |
| Search | Search-related files/indexes | `/search?q=`, noindex, excluded from sitemap | Validate |

## Recommended technical decision before implementation

Do **not** force all pages into the MBA-only hierarchy. The repository contains content about non-MBA programmes (UG, engineering, law, etc.). The proposed architecture is MBA-centric; any migration needs a separate scope decision for non-MBA content so it is not incorrectly redirected, orphaned, or forced into irrelevant MBA paths.

Recommended route families:
- MBA college discovery and profile routes under `/mba-colleges/`
- Entrance exams under `/exams/`
- MBA rankings under `/rankings/`
- Tools under `/tools/`
- Comparisons under `/compare/`
- Guides under `/guides/`
- Non-MBA college/university content: preserve existing URLs initially unless a separate broader architecture is approved

## Next work
- [ ] Crawl the public sitemap (connector could not retrieve the site's sitemap/robots endpoints at audit time; direct network DNS also failed in this runtime).
- [ ] Generate a canonical public URL inventory from `sitemap.xml`, not merely from filenames.
- [ ] Cross-check inventory with HTML files, CMS data, internal link audit, and Search Console export.
- [ ] Classify each route as KEEP, MIGRATE, MERGE/REDIRECT, NOINDEX, REMOVE/410, or NEEDS REVIEW.
- [ ] Build proposed destination and redirect map; verify each mapping manually for content/entity match.
- [ ] Decide MBA-only migration scope versus preservation of non-MBA routes.
- [ ] Implement test route mapping on this branch only after inventory decisions are complete.

## Limitations
This is a repository structural audit. Live HTTP status, response canonical, redirect chains, robots/noindex, internal-link depth, actual rendered route content and Search Console metrics were not verified because the site endpoints were unavailable to the browsing and container network tools at this time. Do not interpret filename-based provisional classifications as a validated public URL list.
