#!/usr/bin/env python3
"""Controlled v8 benchmark test for the first fresh production candidate.

Rank 30 (Institute of Management Technology) is intentionally used instead of
rank 27/29 because rank 27 is protected and rank 29 already has generated
content. This test uses the Google Sheet as the queue authority and does not
force a page type: v8 must generate exactly the page types whose Sheet status
is incomplete.

No AGENTS.md or repository agent configuration is read or executed.
"""
import os

os.environ["COLLEGE_TEST_RANK"] = "30"
os.environ["COLLEGE_BATCH_SIZE"] = "1"

import independent_college_content_agent_v8 as agent

if __name__ == "__main__":
    raise SystemExit(agent.main())
