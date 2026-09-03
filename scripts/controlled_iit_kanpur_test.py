#!/usr/bin/env python3
"""Controlled one-college production test for the independent agent.

This controlled test targets NIRF rank 29 (IIM Visakhapatnam), which is
currently unprocessed. IIT Kanpur (rank 27) is already protected because its
deployment status is ``Already Exists`` and must never be overwritten for a
pipeline test.

The Google Sheet remains authoritative for queue eligibility. The test first
requests a sufficiently large eligible batch, selects rank 29 from that
returned batch, and then narrows execution to that single college. Programme
generation is forced so the complete research -> generation -> QA -> publish
pipeline can be exercised without creating the full college page set.

No AGENTS.md or repository agent configuration is imported or executed.
"""
import run_independent_college_content_agent as runner

TEST_RANK = "29"
TEST_COLLEGE = "indian institute of management visakhapatnam"

original_get_sheet_batch = runner.get_sheet_batch
original_google_get = runner.google_get
original_batch_size = runner.BATCH_SIZE
original_sheet_missing_types = runner.sheet_missing_types

# The deployed Apps Script supports the authenticated assignBatch action.
# Translate the standalone runner's legacy nextBatch request without changing
# the standalone agent itself.
def google_get_via_post(action, **params):
    if action == "nextBatch":
        action = "assignBatch"
    return runner.google_post(action, **params)


def get_controlled_college_only():
    # Ask for a real queue batch first. BATCH_SIZE=1 can return an earlier
    # eligible item (for example a college awaiting QA), so the controlled test
    # must inspect a wider batch before selecting its dedicated test college.
    runner.BATCH_SIZE = max(original_batch_size, 10)
    batch = original_get_sheet_batch()
    selected = [
        x for x in batch
        if str(x.get("rank", "")).strip() == TEST_RANK
        or x.get("college_name", "").strip().lower() == TEST_COLLEGE
    ]
    if not selected:
        raise RuntimeError(
            "Controlled test could not find IIM Visakhapatnam (rank 29) in the eligible Google Sheet batch"
        )
    return selected[:1]


def force_programme_for_test(college, tracker, forced=None):
    return {"programme"}


runner.google_get = google_get_via_post
runner.get_sheet_batch = get_controlled_college_only
runner.BATCH_SIZE = 10
runner.sheet_missing_types = force_programme_for_test

try:
    raise SystemExit(runner.main())
finally:
    runner.google_get = original_google_get
    runner.get_sheet_batch = original_get_sheet_batch
    runner.BATCH_SIZE = original_batch_size
    runner.sheet_missing_types = original_sheet_missing_types
