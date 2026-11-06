# MISSING_DATA.md — CollegeDecoded SEO recovery

Updated: 2026-11-06

This file records factual inputs that must be present before college-page content is rewritten. It deliberately does not guess missing values.

## Source workbook required

The task refers to an attached workbook containing the sheets `All_508`, `Boilerplate_over_50pct`, `Invalid_JSONLD`, and `Non_MBA_pages`. That exact workbook was not available among the current conversation uploads or the searchable Library files at implementation time. The Library contains separate 10-page, 10-low-quality-page, 50-URL deep-dive, and 10-college inventory workbooks; none is a substitute for the 508-URL workbook.

| Required input | Exact information needed | Why it is required |
|---|---|---|
| `All_508` | The exact 508 canonical URLs and any URL-level notes/labels | Stable page-level join key for content, links, sitemap and Search Console reporting |
| `Boilerplate_over_50pct` | Exact 32 page URLs and the 8-word-shingle similarity/boilerplate percentages | Prevents selecting the wrong pages for the first content-rebuild batches |
| `Invalid_JSONLD` | Exact 13 page URLs and the parser/error details, if present | Allows a page-by-page repair and regression test |
| `Non_MBA_pages` | Exact 97 URLs, page intent and any keep/redirect/noindex recommendation already recorded | Needed for a reasoned decision table; no page is excluded by default |

## College-specific factual fields to collect only where absent

For each affected college/programme page, record the source URL and source publication/update date for every value below that the page needs. If the official source does not publish a value, record `Not published by official source reviewed`; do not fill the gap with estimates or third-party claims.

- **Fees:** academic cycle, programme/specialisation, tuition, one-time charges, hostel/mess if applicable, payment schedule and fee-basis caveats.
- **Admissions:** intake/cycle, application opening/closing dates, eligibility, accepted entrance exams, selection stages, required documents and official brochure/notice.
- **Cutoffs:** exam, admission year, programme/category/round, metric type (percentile/score/rank) and official counselling/institute source.
- **Placements:** graduating batch, programme, median/average/highest metric, currency/unit, report/table page, placement denominator and whether the metric is programme-specific or institute-wide.
- **Rankings:** agency, category, edition/year, exact rank and official ranking source.
- **Courses:** official programme name, award, duration, campus, intake and current curriculum/prospectus link.

## Current status

- No college-page factual claims have been added or changed in PR 1.
- The 32-page rebuild, 13-page schema repair mapping, 97-page non-MBA decision table and 508-page link baseline remain gated on the exact workbook.
- Existing repository data in `college-cms/`, `data/` and the affected page source may be used where it is directly attributable. Any field still missing after that source check must be added here with the affected URL and the exact source/document needed.
