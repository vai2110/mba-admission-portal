#!/usr/bin/env python3
"""Exit non-zero when repository-controlled page mutation is frozen."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "freeze.json"

try:
    state = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
except (OSError, json.JSONDecodeError) as exc:
    print(f"AUTOMATION FREEZE: cannot read {CONFIG}: {exc}", file=sys.stderr)
    raise SystemExit(2)

if state.get("freeze_content_automation") or state.get("freeze_page_mutations"):
    print("AUTOMATION FROZEN: page-writing automation is disabled by config/freeze.json", file=sys.stderr)
    raise SystemExit(78)

print("AUTOMATION FREEZE: disabled; page-writing automation may proceed")
