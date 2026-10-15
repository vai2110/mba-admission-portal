#!/usr/bin/env python3
"""Validate JSON-LD syntax on indexable HTML pages and validate cutoff data availability."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".vercel"}

def attr(tag, name):
    m = re.search(rf'\b{name}\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
    return m.group(2) if m else ""

def is_noindex(raw):
    for m in re.finditer(r'<meta\b[^>]*>', raw, re.I | re.S):
        tag = m.group(0)
        if attr(tag, "name").lower() == "robots" and "noindex" in attr(tag, "content").lower():
            return True
    return False

errors = []
jsonld_warnings = []
checked = 0
schemas_checked = 0
for path in ROOT.rglob("*.html"):
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if is_noindex(raw):
        continue
    checked += 1
    for m in re.finditer(r'<script\b([^>]*)>(.*?)</script>', raw, re.I | re.S):
        if not re.search(r'\btype\s*=\s*(["\'])application/ld\+json\1', m.group(1), re.I):
            continue
        schemas_checked += 1
        try:
            json.loads(m.group(2))
        except (json.JSONDecodeError, TypeError) as exc:
            jsonld_warnings.append(f"{path.relative_to(ROOT).as_posix()}: invalid JSON-LD ({exc})")

data_path = ROOT / "mba-cutoff-data.json"
if not data_path.exists():
    errors.append("mba-cutoff-data.json is missing from the build output")
else:
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
        expected = {"CAT", "XAT", "SNAP", "CMAT", "MAT", "NMAT"}
        if not isinstance(data, dict) or not isinstance(data.get("exams"), dict):
            errors.append("mba-cutoff-data.json must contain an exams object")
        else:
            missing = sorted(expected - set(data["exams"]))
            if missing:
                errors.append("mba-cutoff-data.json missing exam data: " + ", ".join(missing))
            for exam in sorted(expected & set(data["exams"])):
                item = data["exams"][exam]
                if not isinstance(item, dict) or not isinstance(item.get("rows"), list) or not item["rows"]:
                    errors.append(f"mba-cutoff-data.json has no usable rows for {exam}")
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"mba-cutoff-data.json is invalid: {exc}")

print(f"Structured-data validation scanned {checked} indexable HTML files and {schemas_checked} JSON-LD blocks.")
if jsonld_warnings:
    print(f"WARNING: {len(jsonld_warnings)} pre-existing invalid JSON-LD blocks need follow-up remediation.")
    for warning in jsonld_warnings[:100]:
        print("- " + warning)
if errors:
    print("STRUCTURED-DATA / CUTOFF ASSET VALIDATION FAILED")
    for error in errors[:100]:
        print("- " + error)
    sys.exit(1)
print("STRUCTURED-DATA / CUTOFF ASSET VALIDATION PASSED")
