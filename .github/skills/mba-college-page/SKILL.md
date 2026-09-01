# MBA College Page Skill

## Purpose

This skill defines the repeatable production method for college overview, course-specific and placement pages in the MBA Portal.

## Inputs

Required: college name.

Optional: specific programme, page type, academic session, requested update, or batch of colleges.

## Required source hierarchy

1. College/university official website.
2. Official programme/admission portal operated by the institution.
3. Official fee notification/prospectus.
4. Official placement report/annual report.
5. Official entrance-test authority.
6. NIRF official release for NIRF data.

Do not use coaching portals, aggregators, blogs or social posts as the authority for numeric claims when an official source is available.

## Page architecture

### College overview

- SEO title and description
- Clean hero with college name + broad student intent
- Quick facts
- College overview
- `<hr/>`
- Important admission dates immediately after overview
- `<hr/>`
- Admission process
- `<hr/>`
- Eligibility and entrance requirements
- `<hr/>`
- Cutoff / shortlist criteria
- `<hr/>`
- Fees and complete cost
- `<hr/>`
- Popular programmes with functional links
- `<hr/>`
- Latest placement highlights
- `<hr/>`
- Placement trend table
- `<hr/>`
- Student-focused decision information
- `<hr/>`
- Specific FAQs
- `<hr/>`
- Official links

### Course page

Focus on the exact programme rather than explaining MBA generally. Include eligibility, entrance route, application, selection stages, fees, seats/intake, important dates, cutoff/shortlisting, programme-specific outcomes and links to official documents.

### Placement page

- SEO title/meta
- H1 without forcing a year into the heading
- Latest placement highlights
- Highest/average/median figures only when officially reported
- Recruiters/roles only when officially reported
- Year-wise placement comparison, maximum three data columns as the default
- Interpretation of the published trend without unsupported conclusions
- Programme/batch context
- Official placement report links

## Data rules

Every number is a claim. Verify it.

For each figure, retain internally:

`metric | value | batch/year | source URL/document | source date/context`

Do not merge numbers from different batches without labelling them.

If an official report gives only average CTC, do not manufacture median CTC. If the institution does not publish a cutoff, say so. If a competitive estimate is useful and explicitly requested, label it `Estimated competitive range — not an official cutoff`.

For fees:

- Separate academic/institutional fee from hostel, mess, deposits, insurance, travel, personal expenses and other charges.
- Mark refundable deposits separately.
- Calculate a full-course total only when the official schedule supports the calculation.
- If later-year charges are not published, do not pretend the final two-year cost is known.

## SEO/AEO/GEO rules

Use natural variants such as:

- `[College] admission [year]`
- `[College] fees`
- `[College] cutoff`
- `[College] placements`
- `[College] admission process`
- `[College] eligibility`
- `[College] fees including hostel`
- `[College] placement package`
- `[College] courses and fees`
- `[College] [city]`

Use long-tail variants only where the page genuinely answers the query. Do not repeat the college name unnaturally.

Answer-first blocks should directly answer high-intent questions in 1–3 sentences before adding detail.

## H2 rules

H2s must be short and search-intent-led. Examples:

- `IIM Mumbai Admission Process`
- `IIM Mumbai MBA Fees`
- `IIM Mumbai Cutoff`
- `IIM Mumbai Placements`
- `IIM Mumbai Important Admission Dates`

Avoid vague H2s such as `Why Choose Us`, `Key Highlights`, `Everything You Need to Know`, or `A Great Opportunity`.

## Hero rules

The hero must contain:

- Full official college name in the H1.
- Clear primary search intent.
- Short supporting line describing the page's actual coverage.
- Location where useful.
- Official website link where the established architecture includes it.

Do not put a short form/abbreviation above the H1. Do not add fake badges, generic slogans, rankings without context, or promotional language.

## Internal-link rules

Before saving:

1. Resolve every destination.
2. If a destination page exists, link it.
3. If the user requested the destination and it does not exist, create it.
4. Never leave placeholder `#` links for functional navigation.
5. Use the exact repository filename convention.

## Search/index rules

The search experience must be data-driven and scalable. A newly created college must be discoverable through:

- full official name
- common short form
- common spelling variant
- city + college where appropriate

Do not solve a search failure with a single hard-coded `if` statement.

## Quality gate

A page is not complete until all are true:

- Source-backed numbers.
- No generic filler.
- Correct dates/session context.
- Fees reconciled or clearly qualified.
- Placement context is explicit.
- H1/H2 hierarchy is logical.
- `<hr/>` separators match the established architecture.
- Mobile and desktop layout is preserved.
- No broken internal links.
- No placeholder functional links.
- Search/index updated where required.
- Official links work.

## Preferred implementation pattern

Reuse the closest approved page as the structural template. Copy structure, not facts. Replace all college-specific facts deliberately. After editing, search the output for the previous college's name, city, URLs, fees, placement figures and programme names to prevent accidental carry-over.
