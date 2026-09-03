#!/usr/bin/env python3
"""Run the independent MBA college content agent from the Google Sheet queue.

Rules:
- Google Sheet is the production queue/status source.
- NIRF ranks 1-26 are never selected for new production.
- The next eligible batch is requested from Apps Script.
- Only those exact ranks are passed to the independent agent.
- After processing, GitHub-side status is synchronized back to the Sheet.
- No existing AGENTS.md or repository agent configuration is imported/executed.
"""

import csv
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import independent_college_content_agent_v7 as agent

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "college-content-master.csv"

GOOGLE_SHEET_WEBAPP_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL", "").strip()
BATCH_SIZE = int(os.getenv("COLLEGE_BATCH_SIZE", "10"))
COMPLETED_UPTO_RANK = 26


def google_get(action, **params):
    if not GOOGLE_SHEET_WEBAPP_URL:
        raise RuntimeError("GOOGLE_SHEET_WEBAPP_URL is missing")

    query = {"action": action}
    query.update(params)
    url = GOOGLE_SHEET_WEBAPP_URL + ("&" if "?" in GOOGLE_SHEET_WEBAPP_URL else "?") + urlencode(query)

    request = Request(url, headers={"User-Agent": "MBA-College-Content-Agent/1.0"})
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not payload.get("success", False):
        raise RuntimeError(payload.get("error", "Google Sheet request failed"))

    return payload


def get_sheet_batch():
    payload = google_get("nextBatch", batchSize=BATCH_SIZE)
    colleges = payload.get("colleges", [])

    if not isinstance(colleges, list):
        raise RuntimeError("Google Sheet returned an invalid college batch")

    selected = []
    for college in colleges:
        try:
            rank = int(str(college.get("rank", "")).strip())
        except (TypeError, ValueError):
            continue

        if rank <= COMPLETED_UPTO_RANK:
            continue

        selected.append({
            "rank": str(rank),
            "college_name": str(college.get("collegeName", "")).strip(),
            "official_website": "",
        })

    return selected


def restrict_agent_to_sheet_batch(rows, selected):
    selected_ranks = {str(x["rank"]) for x in selected}
    selected_names = {x["college_name"].strip().lower() for x in selected if x.get("college_name")}

    ordered = agent.priority_rows(rows)
    restricted = []

    for row in ordered:
        rank = str(row.get("rank", "")).strip()
        name = str(row.get("college_name", "")).strip().lower()

        if rank in selected_ranks or name in selected_names:
            if int(rank) > COMPLETED_UPTO_RANK:
                restricted.append(row)

    # Preserve the exact order returned by Google Sheet.
    by_rank = {str(row.get("rank", "")).strip(): row for row in restricted}
    result = []
    for item in selected:
        row = by_rank.get(str(item["rank"]))
        if row:
            result.append(row)

    return result


def sync_master_to_sheet(selected):
    """Sync final statuses for the selected ranks back to Google Sheet.

    POST is deliberately avoided here because the current Apps Script web app
    is unauthenticated. The agent can still use the public GET queue endpoint.
    Once a token-protected POST endpoint is installed, this function can be
    enabled without changing the production selection logic.
    """
    if not MASTER.exists():
        return

    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    selected_ranks = {str(x["rank"]) for x in selected}

    final_rows = []
    for row in rows:
        if str(row.get("rank", "")).strip() in selected_ranks:
            final_rows.append(row)

    # Print a machine-readable summary for the workflow log.
    print("GOOGLE_SHEET_SYNC_PENDING=" + json.dumps(final_rows, ensure_ascii=False))


def main():
    selected = get_sheet_batch()

    if not selected:
        print("No eligible colleges returned by Google Sheet.")
        return 0

    print("Google Sheet selected batch:")
    for college in selected:
        print(f"- Rank {college['rank']}: {college['college_name']}")

    rows = agent.read_master()
    restricted = restrict_agent_to_sheet_batch(rows, selected)

    if not restricted:
        raise RuntimeError("Google Sheet returned colleges, but none matched the GitHub master list")

    if len(restricted) != len(selected):
        missing = [x["rank"] for x in selected if x["rank"] not in {str(r.get("rank")) for r in restricted}]
        raise RuntimeError("GitHub master is missing Google Sheet ranks: " + ", ".join(missing))

    # Permanently exclude ranks 1-26 at the runner level as a second safety gate.
    restricted = [r for r in restricted if int(str(r.get("rank", "0"))) > COMPLETED_UPTO_RANK]

    if not restricted:
        raise RuntimeError("Safety gate removed the entire selected batch")

    original_priority_rows = agent.priority_rows
    original_batch_size = agent.BATCH_SIZE

    try:
        agent.priority_rows = lambda _rows: restricted
        agent.BATCH_SIZE = len(restricted)
        agent.main()
    finally:
        agent.priority_rows = original_priority_rows
        agent.BATCH_SIZE = original_batch_size

    sync_master_to_sheet(selected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
