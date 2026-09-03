#!/usr/bin/env python3
"""Controlled one-college production test for the independent agent.

The Google Sheet queue remains authoritative, but this test explicitly narrows
that queue to NIRF rank 27 (IIT Kanpur). Programme generation is forced for the
test so an older local tracker or Sheet status cannot suppress it. Existing
HTML files remain protected by the v7 agent.
"""
import run_independent_college_content_agent as runner

# Make the test deterministic: process IIT Kanpur only, regardless of the
# batch size configured in GitHub Actions or returned by the Sheet endpoint.
original_get_sheet_batch = runner.get_sheet_batch
original_google_get = runner.google_get
original_batch_size = runner.BATCH_SIZE
original_sheet_missing_types = runner.sheet_missing_types

# The deployed Apps Script exposes the authenticated batch-assignment operation
# as assignBatch. The standalone runner still asks for nextBatch, so translate
# only that action during this controlled test.
def google_get_via_post(action, **params):
    if action == "nextBatch":
        action = "assignBatch"
    return runner.google_post(action, **params)


def get_iit_kanpur_only():
    batch = original_get_sheet_batch()
    selected = [
        x for x in batch
        if str(x.get("rank", "")).strip() == "27"
        or x.get("college_name", "").strip().lower() == "indian institute of technology kanpur"
    ]
    if not selected:
        raise RuntimeError("Controlled test could not find IIT Kanpur (rank 27) in the Google Sheet batch")
    return selected[:1]


def force_programme_for_test(college, tracker, forced=None):
    return {"programme"}


runner.google_get = google_get_via_post
runner.get_sheet_batch = get_iit_kanpur_only
runner.BATCH_SIZE = 1
runner.sheet_missing_types = force_programme_for_test

try:
    raise SystemExit(runner.main())
finally:
    runner.google_get = original_google_get
    runner.get_sheet_batch = original_get_sheet_batch
    runner.BATCH_SIZE = original_batch_size
    runner.sheet_missing_types = original_sheet_missing_types
