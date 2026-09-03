#!/usr/bin/env python3
"""Controlled one-college production test for the independent agent.

This diagnostic test targets the first genuinely unprocessed college after
rank 26: IIM Visakhapatnam (rank 29). IIT Kanpur (rank 27) is already protected
because its deployment status is ``Already Exists`` and must not be overwritten.

For this controlled diagnostic only, the queue is read through the Apps Script
GET ``nextBatch`` endpoint, which is the endpoint intended for queue discovery.
The test requests a batch of 10 eligible colleges, selects rank 29 from that
returned batch, and then executes exactly one college. Production continues to
use the authenticated POST ``assignBatch`` transport.

No AGENTS.md or repository agent configuration is imported or executed.
"""
import run_independent_college_content_agent as runner

TEST_RANK = "29"
TEST_COLLEGE = "indian institute of management visakhapatnam"

original_get_sheet_batch = runner.get_sheet_batch
original_batch_size = runner.BATCH_SIZE
original_sheet_missing_types = runner.sheet_missing_types


def get_controlled_college_only():
    # Queue discovery uses the deployed GET nextBatch endpoint. Ask for enough
    # rows to include the dedicated test college; execution remains one-college.
    runner.BATCH_SIZE = max(original_batch_size, 10)
    batch = original_get_sheet_batch()
    selected = [
        x for x in batch
        if str(x.get("rank", "")).strip() == TEST_RANK
        or x.get("college_name", "").strip().lower() == TEST_COLLEGE
    ]
    if not selected:
        ranks = ", ".join(str(x.get("rank", "")) for x in batch)
        raise RuntimeError(
            "Controlled test could not find IIM Visakhapatnam (rank 29) in the GET nextBatch results. "
            f"Returned eligible ranks: {ranks or 'none'}"
        )
    return selected[:1]


def force_programme_for_test(college, tracker, forced=None):
    return {"programme"}


runner.get_sheet_batch = get_controlled_college_only
runner.BATCH_SIZE = 10
runner.sheet_missing_types = force_programme_for_test

try:
    raise SystemExit(runner.main())
finally:
    runner.get_sheet_batch = original_get_sheet_batch
    runner.BATCH_SIZE = original_batch_size
    runner.sheet_missing_types = original_sheet_missing_types
