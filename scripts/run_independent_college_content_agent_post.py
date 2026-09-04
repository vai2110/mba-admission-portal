#!/usr/bin/env python3
"""POST-authenticated launcher for the independent college content agent.

The deployed Apps Script currently exposes the batch-assignment operation as
``assignBatch``. The standalone agent asks for ``nextBatch``; this launcher
translates only that queue-read action to the authenticated ``assignBatch``
POST route. It also enforces the current CollegeDecoded markup standard:
student-centric accordion FAQs and <hr> separators between consecutive H2
sections. The standalone agent itself remains unchanged.

No AGENTS.md or repository agent configuration is imported or executed.
"""
import re

import independent_college_content_agent as runner

_original_google_get = runner.google_get
_original_strict_audit = runner.strict_audit
_original_generation = runner.BASE_GENERATION_PROMPT
_original_revision = runner.BASE_REVISION_PROMPT


def google_get_via_post(action, **params):
    # The deployed Web App rejects the legacy nextBatch action. assignBatch
    # returns the selected colleges and is an authenticated POST action in the
    # finalized Apps Script. Keep all other actions unchanged.
    if action == "nextBatch":
        action = "assignBatch"
    return runner.google_post(action, **params)


def generation_prompt_with_markup_rules(college, rank, url, research, types, feedback=""):
    base = _original_generation(college, rank, url, research, types, feedback)
    return base + """

CURRENT SITE MARKUP STANDARD — MANDATORY:
- FAQs must be student-centric and based on real admission/fee/placement/programme questions students are currently likely to ask. Do not use generic FAQ questions such as only 'What is the fee?', 'What is the duration?' or 'Is the college good?'.
- FAQ questions must address decision points such as cutoff vs actual selection, fresher/work-experience implications, fee components or extra costs, placement interpretation, programme choice, admission-process risks, eligibility edge cases, or other college-specific student intent.
- Every FAQ answer must be detailed enough to be useful, written in simple English, and grounded in the supplied official-source material. Never invent a fact to make an FAQ more complete.
- FAQ markup MUST use <details class="accordion"><summary>Question</summary><div class="faq-answer"><p>Fact-based answer...</p></div></details> for every FAQ item. Do not use the old .faq-item-only pattern.
- Put <hr> between every two consecutive H2 sections in the main content. Do not leave adjacent H2 sections without an intervening <hr>.
"""


def revision_prompt_with_markup_rules(college, rank, url, research, types, failures, previous):
    base = _original_revision(college, rank, url, research, types, failures, previous)
    return base + """

CURRENT SITE MARKUP STANDARD — MANDATORY:
- Replace generic FAQ blocks with student-centric, college-specific questions based on real applicant decision points and current admission/placement/fee concerns.
- Answers must be detailed, simple-English and fact based using only supplied official sources.
- Every FAQ item MUST use <details class="accordion"><summary>...</summary><div class="faq-answer"><p>...</p></div></details>.
- Insert <hr> between every pair of consecutive H2 sections in the main content.
"""


def strict_audit_with_markup_rules(html, source_urls, official_url, files, page_type=""):
    score, critical, notes = _original_strict_audit(html, source_urls, official_url, files, page_type)
    faq_section = re.search(r'<section[^>]+id=["\']faq["\'][\s\S]*?</section>', html or "", re.I)
    faq_html = faq_section.group(0) if faq_section else ""
    if faq_html and not re.search(r'<details[^>]+class=["\'][^"\']*accordion', faq_html, re.I):
        critical.append("FAQ section does not use the required accordion class")
        score = max(0, int(score) - 8)
    if faq_html and not re.search(r'<summary>[^<]+</summary>\s*<div[^>]+class=["\'][^"\']*faq-answer', faq_html, re.I):
        critical.append("FAQ accordion markup is incomplete")
        score = max(0, int(score) - 4)
    sections = re.findall(r'<section[^>]+class=["\'][^"\']*main-section[^"\']*["\'][^>]*>[\s\S]*?</section>', html or "", re.I)
    if len(sections) >= 2:
        for a, b in zip(sections, sections[1:]):
            # This deterministic check is intentionally conservative: the
            # separator must appear in the source between the two sections.
            pos_a = html.find(a)
            pos_b = html.find(b, pos_a + len(a))
            between = html[pos_a + len(a):pos_b]
            if not re.search(r'<hr\s*/?>', between, re.I):
                critical.append("Missing <hr> between consecutive H2 sections")
                score = max(0, int(score) - 5)
                break
    return score, list(dict.fromkeys(critical)), list(dict.fromkeys(notes))


runner.google_get = google_get_via_post
runner.BASE_GENERATION_PROMPT = generation_prompt_with_markup_rules
runner.BASE_REVISION_PROMPT = revision_prompt_with_markup_rules
runner.strict_audit = strict_audit_with_markup_rules

try:
    raise SystemExit(runner.main())
finally:
    runner.google_get = _original_google_get
    runner.BASE_GENERATION_PROMPT = _original_generation
    runner.BASE_REVISION_PROMPT = _original_revision
    runner.strict_audit = _original_strict_audit
