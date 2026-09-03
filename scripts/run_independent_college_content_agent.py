#!/usr/bin/env python3
"""Run the independent MBA college content agent from the Google Sheet queue.

Production rules:
- Google Sheet is the live production queue/status source.
- NIRF ranks 1-26 are permanently excluded from new production.
- Only the exact colleges returned by Apps Script are processed.
- Sheet page-status fields are authoritative for deciding which page types are missing.
- Existing HTML files remain protected by the independent agent.
- No AGENTS.md or repository agent configuration is imported/executed.
- A deterministic reference-architecture QA gate is installed before generation.
"""

import csv
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import independent_college_content_agent_v7 as agent
from reference_quality_gate import append_reference_contract, validate_reference_architecture

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "college-content-master.csv"
GOOGLE_SHEET_WEBAPP_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL", "").strip()
GOOGLE_SHEETS_API_SECRET = os.getenv("GOOGLE_SHEETS_API_SECRET", "").strip()
BATCH_SIZE = int(os.getenv("COLLEGE_BATCH_SIZE", "10"))
COMPLETED_UPTO_RANK = 26

BASE_MISSING_TYPES = agent.missing_types
BASE_AUDIT = agent.audit
BASE_GENERATION_PROMPT = agent.generation_prompt
BASE_REVISION_PROMPT = agent.revision_prompt
BASE_NORMALIZE_PAGES = agent.normalize_pages


def google_get(action, **params):
    if not GOOGLE_SHEET_WEBAPP_URL:
        raise RuntimeError("GOOGLE_SHEET_WEBAPP_URL is missing")
    query = {"action": action, **params}
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
    payload = {"secret": GOOGLE_SHEETS_API_SECRET, "action": action, **payload_fields}
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        GOOGLE_SHEET_WEBAPP_URL,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "MBA-College-Content-Agent/1.0"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success", False):
        raise RuntimeError(result.get("error", "Google Sheet update failed"))
    return result


def _field(obj, *names):
    for name in names:
        if name in obj and obj.get(name) not in (None, ""):
            return obj.get(name)
    return ""


def get_sheet_batch():
    payload = google_get("nextBatch", batchSize=BATCH_SIZE)
    colleges = payload.get("colleges", [])
    if not isinstance(colleges, list):
        raise RuntimeError("Google Sheet returned an invalid college batch")

    selected = []
    for college in colleges:
        try:
            rank = int(str(_field(college, "rank", "Rank")).strip())
        except (TypeError, ValueError):
            continue
        if rank <= COMPLETED_UPTO_RANK:
            continue
        selected.append({
            "rank": str(rank),
            "college_name": str(_field(college, "collegeName", "College Name", "college_name")).strip(),
            "official_website": str(_field(college, "officialWebsite", "official_website", "Official Website Links")).strip(),
            "overview_status": str(_field(college, "overviewStatus", "Overview Page", "overview_page")).strip(),
            "placement_status": str(_field(college, "placementStatus", "Placement Page", "placement_page")).strip(),
            "popular_course_status": str(_field(college, "popularCourseStatus", "Popular Course Pages", "popular_course_pages")).strip(),
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
        if (rank in selected_ranks or name in selected_names) and rank.isdigit() and int(rank) > COMPLETED_UPTO_RANK:
            restricted.append(row)
    by_rank = {str(row.get("rank", "")).strip(): row for row in restricted}
    return [by_rank[str(item["rank"])] for item in selected if str(item["rank"]) in by_rank]


def _is_done(value):
    v = str(value or "").strip().lower()
    return v in {"done", "complete", "completed", "already exists", "verified", "published", "live"}


def _is_not_applicable(value):
    v = str(value or "").strip().lower()
    return v in {"n/a", "na", "not applicable", "not required", "none"}


def sheet_missing_types(college, tracker, forced=None):
    """Use Sheet statuses as the production source of truth; fall back safely to the base agent detector."""
    meta = next((x for x in _CURRENT_SELECTED if x["college_name"].strip().lower() == college.strip().lower()), None)
    if not meta:
        return BASE_MISSING_TYPES(college, tracker, forced)

    values = [meta.get("overview_status", ""), meta.get("placement_status", ""), meta.get("popular_course_status", "")]
    if not any(values):
        return BASE_MISSING_TYPES(college, tracker, forced)

    missing = set()
    if not _is_done(meta.get("overview_status")) and not _is_not_applicable(meta.get("overview_status")):
        missing.add("overview")
    if not _is_done(meta.get("placement_status")) and not _is_not_applicable(meta.get("placement_status")):
        missing.add("placement")
    if not _is_done(meta.get("popular_course_status")) and not _is_not_applicable(meta.get("popular_course_status")):
        missing.add("programme")
    return missing


def strict_audit(html, source_urls, official_url, files, page_type=""):
    """Combine the existing content/SEO audit with deterministic reference QA."""
    score, critical, notes = BASE_AUDIT(html, source_urls, official_url, files, page_type)
    penalty, arch_critical, arch_notes, checks = validate_reference_architecture(html, page_type)
    merged_critical = list(dict.fromkeys(list(critical) + list(arch_critical)))
    merged_notes = list(dict.fromkeys(list(notes) + list(arch_notes)))
    final_score = max(0, int(score) - int(penalty))
    failed_checks = [k for k, ok in checks.items() if not ok]
    print(f"Reference QA: type={page_type} base_score={score} architecture_penalty={penalty} final_score={final_score} failed_checks={failed_checks}")
    if merged_critical:
        print("Reference QA blockers:")
        for item in merged_critical:
            print(f"- {item}")
    return final_score, merged_critical, merged_notes


def _known_html_files():
    files = sorted(p.name for p in ROOT.glob("*.html"))
    return files[:250]


def _known_files_contract():
    files = _known_html_files()
    if not files:
        return "KNOWN EXISTING HTML FILES: none"
    return "KNOWN EXISTING HTML FILES (internal links may target only these or another page in the current generated package):\n- " + "\n- ".join(files)


def strict_generation_prompt(college, rank, url, research, types, feedback=""):
    prompt = BASE_GENERATION_PROMPT(college, rank, url, research, types, feedback)
    return append_reference_contract(prompt) + "\n\n" + _known_files_contract()


def strict_revision_prompt(college, rank, url, research, types, failures, previous):
    prompt = BASE_REVISION_PROMPT(college, rank, url, research, types, failures, previous)
    return append_reference_contract(prompt) + "\n\n" + _known_files_contract()


def collision_safe_normalize_pages(pages, college):
    """Normalize generated filenames while preserving every existing HTML file.

    The Sheet is authoritative about which page type is missing. If Gemini
    happens to return an old/generic filename that collides with an existing
    protected file, do not silently discard the page. Give the new page a
    deterministic college-specific unused filename instead.
    """
    normalized = BASE_NORMALIZE_PAGES(pages, college)
    reserved = {p.name for p in ROOT.glob("*.html")}
    used = set(reserved)
    mapping = {}
    college_slug = re.sub(r"[^a-z0-9]+", "-", str(college or "").lower()).strip("-")

    for page in normalized:
        old = Path(str(page.get("filename", "")).strip()).name
        if not old or old not in used:
            used.add(old)
            continue

        page_type = str(page.get("type", "programme")).strip().lower()
        title_slug = re.sub(r"[^a-z0-9]+", "-", str(page.get("title", "")).lower()).strip("-")
        if page_type == "overview":
            stem = f"{college_slug}-overview"
        elif page_type == "placement":
            stem = f"{college_slug}-placements"
        else:
            stem = f"{college_slug}-{title_slug or 'mba-programme'}"
        candidate = f"{stem}.html"
        n = 2
        while candidate in used:
            candidate = f"{stem}-{n}.html"
            n += 1
        page["filename"] = candidate
        mapping[old] = candidate
        used.add(candidate)
        print(f"Filename collision protected: {old} -> {candidate}")

    if mapping:
        for page in normalized:
            html = str(page.get("html", ""))
            for old, new in mapping.items():
                html = re.sub(rf'([\"\'(]){re.escape(old)}([\"\')#?])', rf'\1{new}\2', html)
            page["html"] = html
    return normalized


def install_quality_gate():
    agent.audit = strict_audit
    agent.generation_prompt = strict_generation_prompt
    agent.revision_prompt = strict_revision_prompt
    agent.normalize_pages = collision_safe_normalize_pages
    print("Installed deterministic reference-architecture QA gate v1.3")


def mark_batch_researching(selected):
    for college in selected:
        google_post("updateStatus", rank=int(college["rank"]), researchStatus="Researching")
        print(f"Sheet status: rank {college['rank']} -> Researching")


def read_final_statuses(selected):
    if not MASTER.exists():
        return []
    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected_ranks = {str(x["rank"]) for x in selected}
    return [row for row in rows if str(row.get("rank", "")).strip() in selected_ranks]


def sync_master_to_sheet(selected):
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
        print(f"Sheet sync: rank {rank} | quality={quality_score} | research={row.get('research_status')} | qa={row.get('qa_status')} | deployment={row.get('deployment_status')} | live={row.get('live_verification')}")
    missing = selected_ranks - synced_ranks
    if missing:
        raise RuntimeError("Could not sync selected ranks: " + ", ".join(sorted(missing, key=int)))


_CURRENT_SELECTED = []


def main():
    global _CURRENT_SELECTED
    install_quality_gate()
    selected = get_sheet_batch()
    if not selected:
        print("No eligible colleges returned by Google Sheet.")
        return 0
    print("Google Sheet selected batch:")
    for college in selected:
        print(f"- Rank {college['rank']}: {college['college_name']}")

    _CURRENT_SELECTED = selected
    rows = agent.read_master()
    restricted = restrict_agent_to_sheet_batch(rows, selected)
    if not restricted:
        raise RuntimeError("Google Sheet returned colleges, but none matched the GitHub master list")
    if len(restricted) != len(selected):
        missing = [x["rank"] for x in selected if x["rank"] not in {str(r.get("rank")) for r in restricted}]
        raise RuntimeError("GitHub master is missing Google Sheet ranks: " + ", ".join(missing))

    mark_batch_researching(selected)
    original_priority_rows = agent.priority_rows
    original_batch_size = agent.BATCH_SIZE
    original_missing_types = agent.missing_types
    original_normalize_pages = agent.normalize_pages
    try:
        agent.priority_rows = lambda _rows: restricted
        agent.BATCH_SIZE = len(restricted)
        agent.missing_types = sheet_missing_types
        agent.normalize_pages = collision_safe_normalize_pages
        agent.main()
    finally:
        agent.priority_rows = original_priority_rows
        agent.BATCH_SIZE = original_batch_size
        agent.missing_types = original_missing_types
        agent.normalize_pages = original_normalize_pages
        _CURRENT_SELECTED = []

    sync_master_to_sheet(selected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
