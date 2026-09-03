#!/usr/bin/env python3
"""Controlled one-college production test for the independent agent.

The Google Sheet queue remains authoritative, but this test explicitly narrows
that queue to NIRF rank 27 (IIT Kanpur). Programme generation is forced for the
test so an older local tracker cannot suppress it. Existing HTML files remain
protected by the v7 agent.
"""
import run_independent_college_content_agent as runner

# Make the test deterministic: process IIT Kanpur only, regardless of the
# batch size configured in GitHub Actions or returned by the Sheet endpoint.
original_get_sheet_batch = runner.get_sheet_batch
original_batch_size = runner.BATCH_SIZE
original_missing_types = runner.agent.missing_types


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


runner.get_sheet_batch = get_iit_kanpur_only
runner.BATCH_SIZE = 1
runner.agent.missing_types = force_programme_for_test

try:
    raise SystemExit(runner.main())
finally:
    runner.get_sheet_batch = original_get_sheet_batch
    runner.BATCH_SIZE = original_batch_size
    runner.agent.missing_types = original_missing_types
