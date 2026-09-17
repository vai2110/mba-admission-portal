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
Hero; Overview; **Tentative Admission Dates for the 2027-29 cycle immediately after Overview**; Courses/Programmes; Eligibility; Detailed Admission Process; Entrance Exam; Selection Criteria; Cutoff; Fees; Fee Bifurcation; **What the Fee Covers; What the Fee Does Not Cover; Total Course-period Cost**; Placements; Popular Programmes; Student Decision Factors; FAQs; Official Sources.

## Required course-page structure
Hero; Quick Answer; Programme Overview; **Tentative Admission Dates for the 2027-29 cycle immediately after Programme Overview**; Eligibility; Detailed Admission Process; Entrance Exam; Selection Criteria; Cutoff/qualifying threshold; Fees; Fee Bifurcation; **What the Fee Covers; What the Fee Does Not Cover; Total Course-period Cost**; Curriculum; Programme Structure; Programme-specific Placement/Career Information where available; Who Should Apply/Decision Factors; FAQs; Official Sources.

## Required placement-page structure
Hero; Latest Placement Highlights; Placement Snapshot; **latest completed graduating/pass-out batch statistics**; year-wise comparison for **at least 3 comparable years** where official data exists; Average CTC; Median CTC; Highest CTC; Placement Rate where officially reported; Recruiters/offers where officially reported; function/sector data where officially reported; placement trends; programme-specific interpretation; FAQs; Official Sources.

## Factual rules
- Prefer current official institute website, official admission portal, official brochure/notification, official fee document and official placement report.
- Every material number/date/fee/cutoff/seat figure must have an authoritative source trail.
- Never invent a cutoff, fee, placement statistic, seat count or date.
- If an official cutoff is not published, say so. If a future date is unavailable, label any editorial estimate as **tentative** and base it only on a clearly stated previous official cycle; never present it as an official date.
- Tentative 2027-29 dates must be clearly labelled **tentative / expected based on the latest relevant official cycle**, never as announced dates.
- Distinguish qualifying cutoff from competitive/expected target. Never label an estimate as an official cutoff.
- Separate programme fees from additional student-incurred costs and refundable deposits.
- The fee bifurcation must explicitly identify **what is included/covered** and **what is excluded/not covered**, using official fee documents wherever possible. Do not infer inclusions from generic college practice.
- Placement statistics must belong to the **latest completed graduating/pass-out batch** represented by the latest official placement report available for the programme/institute. Clearly label the batch/year.
- Latest placement snapshot should include, where officially reported: **average CTC, median CTC, highest CTC and placement rate**. If any metric is not officially reported, state that it is not reported instead of substituting another metric.
- Year-wise placement comparison should cover **at least 3 years** where comparable official data exists. Keep definitions consistent; flag any methodology/reporting changes.
- Never use another programme's placement data as if it belonged to the target programme.

## Content rules
- No generic filler. Replace claims such as "world-class", "holistic", "excellent placements", "vibrant campus" and similar promotional language with a specific sourced fact or remove them.
- Write for a student making an application/college decision, not for an institutional brochure.
- Use concise, search-intent H2s and useful long-tail coverage naturally.
- H2s must be short, keyword-led and student-intent focused. Avoid vague constructions such as "What Students Can Study", "How Students Should Read...", "What the Programme Is" and similar generic phrasing when a direct keyword heading can answer the intent.
- Use a mix of paragraphs, bullets and tables; tables only where comparison or exact figures benefit the reader.
- **Admission process must be detailed but crisp:** present the actual sequence, eligibility/checks, application, entrance route, shortlist/selection stages, offer/admission and important student actions without padding.
- **FAQs are mandatory and must use an accordion UI/class.** Each FAQ answer must be detailed enough to resolve the student's question, specific to the college/programme, and based on verified facts. Do not use generic MBA FAQ questions/answers. Accordion interaction must be keyboard-accessible, mobile-friendly and must not create horizontal overflow.
- **Bold important decision-useful points, numbers, dates, fees, cutoffs and placement figures** so students can scan the page quickly. Do not bold entire paragraphs or over-format.
- Add `<hr/>` between consecutive H2 sections according to the locked site architecture.
- **Quick Answer must appear exactly once per page.** Do not duplicate a hero summary as a second Quick Answer card. The overview page may use one answer-first block immediately before the main content; course and placement pages should use one concise, factual answer block only.
- **Hero must stay compact and text-first, following the SIBM Pune benchmark.** Use a restrained hero height/padding, one clear H1, a short supporting H2 and source/location line. Do not add bulky statistic panels, logos or decorative modules inside the hero.

## Fees presentation contract
Every relevant overview/course page must contain a **Fee Bifurcation table** when official fee data is available. At minimum, structure it to distinguish applicable components such as tuition/programme fee, hostel/accommodation, mess, refundable deposits and other mandatory charges where officially reported. Add separate, clearly labelled **What the Fee Covers** and **What the Fee Does Not Cover** sections. Include the **total course-period cost** only when it can be calculated safely from official figures, and explain exclusions/assumptions.

## Placement presentation contract
The latest placement section must be answer-first and clearly identify the latest completed pass-out batch. Show a compact placement snapshot with **average CTC, median CTC, highest CTC and placement rate**, subject to official availability. Follow it with a **minimum 3-year year-wise placement comparison table** whenever three comparable official years can be sourced. Do not mix final placements, summer placements, internships or different programmes without explicit labelling.

## Admission-date contract
For every page where a 2027-29 admission cycle is relevant, place a **Tentative Admission Dates: 2027-29** section **immediately after the Overview/Programme Overview section**. Use only evidence-based tentative dates derived from the latest official cycle when the 2027-29 schedule is not yet announced. Every row must state its status (for example, tentative/not announced) where necessary. Once official dates become available, replace tentative entries with the official schedule and source.

## On This Page navigation contract
- The **On This Page** control must appear **only after the hero container**, never inside the hero.
- On desktop it should remain compact and aligned to the right edge of the content area.
- On mobile it must occupy **less than 30% of the viewport width**, sit at the **right-most top position immediately after the hero**, and become sticky while the user scrolls **up or down** through the content.
- The control must contain the page's relevant section links/dropdown options and link to actual section IDs.
- When the user selects an option, **smooth-scroll/redirect to that section and automatically fold/collapse the On This Page control** after selection.
- The sticky control must not cover headings, tables or important content and must not introduce horizontal overflow.
- Do not duplicate another sticky navigation component for the same purpose.

## Mobile table contract — HARD REQUIREMENT
- **Every table must be fully viewable within the mobile viewport without horizontal scrolling.**
- No table may require a horizontal scrollbar or an `overflow-x:auto` interaction on mobile.
- Tables must use responsive widths, fixed/controlled layout where appropriate, wrapped text, sensible column proportions and compact typography.
- Long labels and URLs must wrap (`overflow-wrap:anywhere`/equivalent); cells must not force the document wider than the viewport.
- If a table contains too many columns to remain genuinely readable, restructure it into a mobile-safe stacked/key-value format rather than introducing a horizontal scroller.
- Verify the actual rendered structure at mobile widths during QA, not merely the presence of responsive CSS.

## SEO/AEO/GEO
- One clear, search-intent H1 per page.
- Placement-page H1s must not include a placement year. Put the latest year in the supporting copy, metadata where useful, tables and section headings instead.
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
- **FAQ accordion exists and works.**
- **Fee bifurcation + covered/not-covered fee information exists where applicable.**
- **2027-29 tentative admission section appears immediately after overview/programme overview where relevant.**
- **Latest pass-out placement snapshot includes the required metrics where officially reported.**
- **Year-wise placement comparison covers at least 3 comparable years where official data exists.**
- **On This Page control meets sticky/collapse/mobile-width behaviour.**
- **No mobile horizontal table scrolling.**
- **Important decision-useful information is appropriately bolded.**
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

## Locked Hero, Quick Answer and H2 Rules
- Use the SIBM Pune hero container as the benchmark: compact text-first hero, same proportions, spacing and established typography; never redesign it independently.
- Use the IIM Ahmedabad/SIBM Pune approved `Arial, Helvetica, sans-serif` font stack.
- For the current locked portal scale, use **IIM Ahmedabad typography for body/content:** body 14px, H2 24px desktop, H3 17px, table 13px; use the established mobile reductions.
- For heroes, use the SIBM structure but the IIM Ahmedabad visual type scale: H1 34px desktop, supporting H2 17px, location 13px; mobile H1 26px, H2 13px, location 11px.
- Exactly one visible Quick Answer block per page; remove duplicate introductory answer blocks.
- H2s must be short, specific, student-intent driven and naturally keyword optimised, never generic filler.
- Placement H1s must be concise and keyword-led; keep year-specific details in metadata/body.
- These are hard QA rules for every new page and every existing-page modification.

## Locked Hero HTML Structure
- Match the SIBM Pune hero HTML pattern: one compact hero container, one search-intent H1, one concise supporting H2 and one location/official-site line.
- Do not add fact cards, logos, badges or other modules inside the hero unless the benchmark architecture explicitly contains them.
- Use the approved Arial font stack and the locked type scale above.
- Exactly one Quick Answer block is permitted in visible page content.
- H2s elsewhere must remain short, specific and keyword-led.
