#!/usr/bin/env python3
"""Run the independent MBA college content agent from the Google Sheet queue.

Production rules:
- Google Sheet is the live production queue/status source.
- NIRF ranks 1-26 are permanently excluded from new production.
- The next eligible batch is requested from Apps Script.
- Only those exact ranks are passed to the independent agent.
- Selected colleges are marked as Researching before generation starts.
- Final research/QA/deployment/quality/live-verification status is synced back.
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
GOOGLE_SHEETS_API_SECRET = os.getenv("GOOGLE_SHEETS_API_SECRET", "").strip()
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


def google_post(action, **payload_fields):
    if not GOOGLE_SHEET_WEBAPP_URL:
        raise RuntimeError("GOOGLE_SHEET_WEBAPP_URL is missing")
    if not GOOGLE_SHEETS_API_SECRET:
        raise RuntimeError("GOOGLE_SHEETS_API_SECRET is missing")

    payload = {
        "secret": GOOGLE_SHEETS_API_SECRET,
        "action": action,
        **payload_fields,
    }

    body = json.dumps(payload).encode("utf-8")
    request = Request(
        GOOGLE_SHEET_WEBAPP_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MBA-College-Content-Agent/1.0",
        },
        method="POST",
    )

    with urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("success", False):
        raise RuntimeError(result.get("error", "Google Sheet update failed"))

    return result


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


def mark_batch_researching(selected):
    """Lock the selected colleges in the Sheet before expensive generation."""
    for college in selected:
        google_post(
            "updateStatus",
            rank=int(college["rank"]),
            researchStatus="Researching",
        )
        print(f"Sheet status: rank {college['rank']} -> Researching")


def read_final_statuses(selected):
    if not MASTER.exists():
        return []

    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    selected_ranks = {str(x["rank"]) for x in selected}
    return [
        row for row in rows
        if str(row.get("rank", "")).strip() in selected_ranks
    ]


def sync_master_to_sheet(selected):
    """Write the agent's final per-college status fields to Google Sheet."""
    final_rows = read_final_statuses(selected)

    if not final_rows:
        raise RuntimeError("No final status rows found in GitHub master tracker for selected batch")

    selected_ranks = {str(x["rank"]) for x in selected}
    synced_ranks = set()

    for row in final_rows:
        rank = str(row.get("rank", "")).strip()
        if rank not in selected_ranks:
            continue

        raw_score = str(row.get("quality_score", "")).strip()
        quality_score = None
        try:
            quality_score = float(raw_score)
            if quality_score.is_integer():
                quality_score = int(quality_score)
        except (TypeError, ValueError):
            pass

        google_post(
            "updateStatus",
            rank=int(rank),
            overviewStatus=str(row.get("overview_status", "")).strip(),
            placementStatus=str(row.get("placement_status", "")).strip(),
            popularCourseStatus=str(row.get("popular_course_status", "")).strip(),
            qualityScore=quality_score,
            researchStatus=str(row.get("research_status", "")).strip(),
            qaStatus=str(row.get("qa_status", "")).strip(),
            deploymentStatus=str(row.get("deployment_status", "")).strip(),
            liveVerification=str(row.get("live_verification", "")).strip(),
        )
        synced_ranks.add(rank)
        print(
            f"Sheet sync: rank {rank} | quality={quality_score} | "
            f"research={row.get('research_status')} | qa={row.get('qa_status')} | "
            f"deployment={row.get('deployment_status')} | live={row.get('live_verification')}"
        )

    missing = selected_ranks - synced_ranks
    if missing:
        raise RuntimeError("Could not sync selected ranks: " + ", ".join(sorted(missing, key=int)))


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
        missing = [
            x["rank"] for x in selected
            if x["rank"] not in {str(r.get("rank")) for r in restricted}
        ]
        raise RuntimeError("GitHub master is missing Google Sheet ranks: " + ", ".join(missing))

    # Permanently exclude ranks 1-26 at the runner level as a second safety gate.
    restricted = [r for r in restricted if int(str(r.get("rank", "0"))) > COMPLETED_UPTO_RANK]

    if not restricted:
        raise RuntimeError("Safety gate removed the entire selected batch")

    # Prevent accidental double-processing if the same workflow is retried.
    mark_batch_researching(selected)

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
