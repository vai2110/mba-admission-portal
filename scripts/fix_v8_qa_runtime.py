#!/usr/bin/env python3
"""Final runtime sanity patch for the standalone V8 benchmark.

This script only edits the standalone V8 agent. It does not read, import,
execute, or follow AGENTS.md or any other repository agent configuration.
"""
from pathlib import Path

p = Path("scripts/independent_college_content_agent_v8.py")
s = p.read_text(encoding="utf-8")
# Normalize both possible escaped forms to the intended regex.
s = s.replace('re.compile(r"college-page\\\\.css")', 're.compile(r"college-page\\.css")')
s = s.replace('re.compile(r"college-page\\.css")', 're.compile(r"college-page\\.css")')
p.write_text(s, encoding="utf-8")
print("V8 QA regex sanity patch applied")
