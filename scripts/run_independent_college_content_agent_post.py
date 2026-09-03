#!/usr/bin/env python3
"""POST-authenticated launcher for the independent college content agent.

The Apps Script queue exposes authenticated mutations through doPost. This
launcher keeps the existing standalone agent unchanged and only replaces the
queue-read transport so nextBatch is requested through the same authenticated
POST endpoint as updateStatus.

No AGENTS.md or repository agent configuration is imported or executed.
"""
import run_independent_college_content_agent as runner

_original_google_get = runner.google_get


def google_get_via_post(action, **params):
    return runner.google_post(action, **params)


runner.google_get = google_get_via_post

try:
    raise SystemExit(runner.main())
finally:
    runner.google_get = _original_google_get
