#!/usr/bin/env python3
"""POST-authenticated launcher for the independent college content agent.

The deployed Apps Script currently exposes the batch-assignment operation as
``assignBatch``. The standalone agent asks for ``nextBatch``; this launcher
translates only that queue-read action to the authenticated ``assignBatch``
POST route. The standalone agent itself remains unchanged.

No AGENTS.md or repository agent configuration is imported or executed.
"""
import run_independent_college_content_agent as runner

_original_google_get = runner.google_get


def google_get_via_post(action, **params):
    # The deployed Web App rejects the legacy nextBatch action. assignBatch
    # returns the selected colleges and is an authenticated POST action in the
    # finalized Apps Script. Keep all other actions unchanged.
    if action == "nextBatch":
        action = "assignBatch"
    return runner.google_post(action, **params)


runner.google_get = google_get_via_post

try:
    raise SystemExit(runner.main())
finally:
    runner.google_get = _original_google_get
