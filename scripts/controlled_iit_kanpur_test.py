#!/usr/bin/env python3
"""Controlled one-college production test for the independent agent.

The previous IIT Kanpur test is intentionally moved to the first genuinely
unprocessed queue item, NIRF rank 29 (IIM Visakhapatnam). IIT Kanpur (rank 27)
is already protected by the production safety rules because its deployment
status is ``Already Exists``; it must not be overwritten merely for testing.

The Google Sheet queue remains authoritative for eligible-college selection.
Programme generation is forced for this controlled test so the pipeline can
exercise research -> generation -> QA -> publish decisions on a college that
has not already been deployed. Existing HTML files remain protected.
"""
import run_independent_college_content_agent as runner

# Make the test deterministic: process IIM Visakhapatnam (rank 29), regardless
# of the batch size configured in GitHub Actions or returned by the Sheet.
original_get_sheet_batch = runner.get_sheet_batch
original_google_get = runner.google_get
original_batch_size = runner.BATCH_SIZE
original_sheet_missing_types = runner.sheet_missing_types

# The Apps Script queue exposes the authenticated batch-assignment operation
# as assignBatch. The standalone runner still asks for nextBatch, so translate
# only that action during this controlled test.
def google_get_via_post(action, **params):
    if action == "nextBatch":
        action = "assignBatch"
    return runner.google_post(action, **params)


def get_controlled_college_only():
    batch = original_get_sheet_batch()
    selected = [
        x for x in batch
        if str(x.get("rank", "")).strip() == "29"
        or x.get("college_name", "").strip().lower() == "indian institute of management visakhapatnam"
    ]
    if not selected:
        raise RuntimeError("Controlled test could not find IIM Visakhapatnam (rank 29) in the eligible Google Sheet batch")
    return selected[:1]


def force_programme_for_test(college, tracker, forced=None):
    return {"programme"}


runner.google_get = google_get_via_post
runner.get_sheet_batch = get_controlled_college_only
runner.BATCH_SIZE = 1
runner.sheet_missing_types = force_programme_for_test

try:
    raise SystemExit(runner.main())
finally:
    runner.google_get = original_google_get
    runner.get_sheet_batch = original_get_sheet_batch
    runner.BATCH_SIZE = original_batch_size
    runner.sheet_missing_types = original_sheet_missing_types
