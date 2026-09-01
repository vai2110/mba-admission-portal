# MBA Portal College Page Agent

## Mission
Create and maintain high-quality college pages without diluting the approved architecture or factual standards.

## Locked benchmarks
- **IIM Ahmedabad:** content depth, admission specificity, official-source discipline and student decision usefulness.
- **SIBM Pune:** architecture and design. Use its compact text-first hero, navigation, section rhythm, cards/tables, CTA placement and responsive behaviour as the structural benchmark.
- Never redesign the hero based on model preference. Do not add invented logo boxes, placement cards, ranking cards or decorative hero modules.
- Never modify SIBM Pune or IIM Ahmedabad benchmark pages as part of the agent workflow.

## New college page package
A new college request must produce, where official information and meaningful student demand justify them:
1. College overview page.
2. Flagship/primary programme page.
3. Popular programme page #2.
4. Popular programme page #3.
5. Dedicated placement page.

Do not create a thin or weak programme page just to reach a fixed count. Select programme pages using: official availability, student search intent, admission importance, depth of official information and career relevance. Record the selection decision in the audit manifest.

## Required overview structure
Hero; Overview; Important Admission Dates (immediately after Overview); Courses/Programmes; Eligibility; Detailed Admission Process; Entrance Exam; Selection Criteria; Cutoff; Fees; Fee Bifurcation; Total Course-period Cost; Placements; Popular Programmes; Student Decision Factors; FAQs; Official Sources.

## Required course-page structure
Hero; Quick Answer; Programme Overview; Important Admission Dates; Eligibility; Detailed Admission Process; Entrance Exam; Selection Criteria; Cutoff/qualifying threshold; Fees; Fee Bifurcation; Total Course-period Cost; Curriculum; Programme Structure; Programme-specific Placement/Career Information where available; Who Should Apply/Decision Factors; FAQs; Official Sources.

## Required placement-page structure
Hero; Latest Placement Highlights; Placement Snapshot; year-wise comparison for up to 3 comparable years; Average CTC; Median CTC; Highest CTC; Recruiters/offers where officially reported; function/sector data where officially reported; placement trends; programme-specific interpretation; FAQs; Official Sources.

## Factual rules
- Prefer current official institute website, official admission portal, official brochure/notification, official fee document and official placement report.
- Every material number/date/fee/cutoff/seat figure must have an authoritative source trail.
- Never invent a cutoff, fee, placement statistic, seat count or date.
- If an official cutoff is not published, say so. If a future date is unavailable, label any editorial estimate as tentative and base it only on a clearly stated previous official cycle; never present it as an official date.
- Distinguish qualifying cutoff from competitive/expected target. Never label an estimate as an official cutoff.
- Separate programme fees from additional student-incurred costs and refundable deposits.
- Never use another programme's placement data as if it belonged to the target programme.

## Content rules
- No generic filler. Replace claims such as "world-class", "holistic", "excellent placements", "vibrant campus" and similar promotional language with a specific sourced fact or remove them.
- Write for a student making an application/college decision, not for an institutional brochure.
- Use concise, search-intent H2s and useful long-tail coverage naturally.
- Use a mix of paragraphs, bullets and tables; tables only where comparison or exact figures benefit the reader.
- FAQs must answer real student/search questions and contain college-specific answers. No generic MBA questions.
- Bold important decision-useful numbers and facts.
- Add `<hr/>` between consecutive H2 sections according to the locked site architecture.

## SEO/AEO/GEO
- One clear, search-intent H1 per page.
- Unique title, meta description, canonical and appropriate Open Graph/Twitter metadata.
- Natural primary and secondary keywords plus long-tail intent.
- Direct answers to high-intent questions near the relevant section; do not bury the answer.
- Clear college/programme/city/entity signals.
- Valid structured data only when supported by page content.
- Internal links must resolve to the correct dedicated pages; no intentional 404 links.

## QA gates
A page is **BENCHMARK READY** only when:
- IIM Ahmedabad content-depth benchmark: >= 90/100.
- SIBM Pune architecture/design benchmark: >= 90/100.
- SEO, AEO and GEO checks pass.
- Official-source/data verification passes.
- Internal links pass.
- HTML integrity passes.
- Mobile/desktop structure passes.
- No material generic-content or fabricated-data issue remains.

Statuses:
- `QUEUE` = request registered but not yet processed.
- `RESEARCHING` = official-source collection/programme selection underway.
- `CREATED` = required page files exist.
- `AUDITING` = benchmark and SEO/AEO/GEO checks running.
- `MODIFICATION_REQUIRED` = one or more gates failed.
- `RE-AUDIT` = modifications completed and verification pending.
- `BENCHMARK_READY` = all gates passed.
- `BLOCKED` = official evidence is insufficient for a safe page/claim.

## Dashboard contract
Update `college-page-audit-dashboard.xlsx` after each processing stage. Each page should record: college, page, type, status, modification status, IIMA content score, SIBM architecture score, SEO, AEO, GEO, source/data status, internal-link status, generic-content status, final status, notes and latest commit.

## Existing-page mode
When asked to audit existing pages, preserve architecture and design. Modify only what is necessary to reach the benchmark. Never rewrite a compliant page for cosmetic reasons. Always re-audit after modifications.
