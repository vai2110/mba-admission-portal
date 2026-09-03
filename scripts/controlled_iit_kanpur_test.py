#!/usr/bin/env python3
"""Controlled one-college production test for the independent agent.

The Google Sheet queue remains authoritative for selection. Exactly one
college is processed. Programme generation is forced for this test so an
older local tracker cannot suppress it. Existing HTML files remain protected
by the v7 agent.
"""
import run_independent_college_content_agent as runner

runner.BATCH_SIZE = 1

original_missing_types = runner.agent.missing_types

def force_programme_for_test(college, tracker, forced=None):
    return {"programme"}

runner.agent.missing_types = force_programme_for_test

try:
    raise SystemExit(runner.main())
finally:
    runner.agent.missing_types = original_missing_types
