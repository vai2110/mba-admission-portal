# IIM Ahmedabad URL Architecture Preview Cluster

**Status:** Preview-only implementation on `seo/url-architecture-migration`. This is not a production migration.

The four pages below are copies of the existing IIM Ahmedabad content pages, with internal links rewritten to the proposed hierarchy where applicable. Every preview page is explicitly **noindex,follow**, has a self-referencing canonical, and is excluded from the sitemap by the existing sitemap generator. The original flat pages remain unchanged and no redirects are introduced.

| Existing route | Preview route | Source page |
|---|---|---|
| `/iim-ahmedabad` | `/mba-colleges/iim-ahmedabad` | `iim-ahmedabad.html` |
| `/iim-ahmedabad-mba-pgp` | `/mba-colleges/iim-ahmedabad/mba` | `iim-ahmedabad-mba-pgp.html` |
| `/iim-ahmedabad-placements` | `/mba-colleges/iim-ahmedabad/placements` | `iim-ahmedabad-placements.html` |
| `/iim-ahmedabad-courses-fees` | `/mba-colleges/iim-ahmedabad/fees` | `iim-ahmedabad-courses-fees.html` |

Each preview page includes a navigation strip linking the cluster. This helps verify nested directory-index routing, clean URLs, canonical metadata, noindex, and entity-specific content in a Vercel preview before mapping more pages.

## QA checklist

- [ ] Preview routes return HTTP 200 (profile/MBA/placements/fees)
- [ ] Each route renders the correct IIM Ahmedabad page title and H1
- [ ] Canonical points to the matching slashless preview route
- [ ] Robots contains `noindex,follow`
- [ ] Preview routes are absent from generated sitemap
- [ ] Cluster navigation links resolve to all four routes
- [ ] Old flat URLs still return their existing pages (no redirects yet)
- [ ] No cross-college content or canonical mismatch

**No production redirects, canonical changes, or old-route removals are part of this preview.**