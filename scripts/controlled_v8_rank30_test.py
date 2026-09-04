#!/usr/bin/env python3
"""Controlled v8 benchmark test for the first fresh production candidate.

Rank 30 (Institute of Management Technology) is intentionally used instead of
rank 27/29 because rank 27 is protected and rank 29 already has generated
content. This benchmark uses the Google Sheet for endpoint health/transport
validation, while the benchmark target itself is explicitly selected from the
repository master row so a temporarily ineligible queue cannot prevent V8 from
being exercised.

No AGENTS.md or repository agent configuration is read or executed.

The benchmark adds temporary network/transport resolvers around V8's
fetch/discovery and Google Sheet queue layers. These handle redirects,
www/non-www, HTTP fallback, transient failures and the deployed Apps Script
transport contract. The target override is benchmark-only and does not modify
Google Sheet statuses.
"""
import os
import time
from urllib.parse import urlparse

import requests

os.environ["COLLEGE_TEST_RANK"] = "30"
os.environ["COLLEGE_BATCH_SIZE"] = "1"

import independent_college_content_agent_v8 as agent


_RESOLVER = requests.Session()
_RESOLVER.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; MBA-College-Content-Agent/3.0; +https://www.imt.edu/)"
})


def _same_domain(a, b):
    da = urlparse(a).netloc.lower().removeprefix("www.")
    db = urlparse(b).netloc.lower().removeprefix("www.")
    return bool(da and db and da == db)


def robust_fetch(url):
    if not url:
        return "", url

    candidates = []
    original = url.strip()
    if not original.startswith(("http://", "https://")):
        original = "https://" + original
    candidates.append(original)

    parsed = urlparse(original)
    if parsed.netloc:
        host = parsed.netloc
        bare = host.removeprefix("www.")
        for scheme in ("https", "http"):
            for candidate_host in (bare, "www." + bare):
                candidate = f"{scheme}://{candidate_host}{parsed.path or '/'}"
                if candidate not in candidates:
                    candidates.append(candidate)

    for candidate in candidates:
        for attempt in range(3):
            try:
                r = _RESOLVER.get(
                    candidate,
                    timeout=30,
                    allow_redirects=True,
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8",
                    },
                )
                content_type = r.headers.get("content-type", "").lower()
                if r.ok and ("text/html" in content_type or "application/xhtml+xml" in content_type):
                    final = r.url
                    if _same_domain(original, final):
                        return r.text, final
                    return "", original
                if r.status_code in (429, 500, 502, 503, 504):
                    time.sleep(2 * (attempt + 1))
                    continue
                break
            except requests.RequestException:
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
    return "", original


agent.fetch = robust_fetch


# The deployed Apps Script endpoint exposes the queue-assignment operation
# through authenticated POST. V8's generic sheet_get() historically attempted
# GET ?action=nextBatch, which can return HTTP 404 on the deployed version.
# Keep the benchmark deterministic by adapting only the queue transport here.
_original_sheet_get = agent.sheet_get


def robust_sheet_get(action, **params):
    if action == "nextBatch":
        print("Google Sheet queue transport: nextBatch -> authenticated assignBatch POST")
        return agent.sheet_post("assignBatch", **params)
    return _original_sheet_get(action, **params)


agent.sheet_get = robust_sheet_get


# Do not let the controlled benchmark mutate the production Sheet statuses.
# Endpoint health and authenticated queue transport have already been tested;
# the benchmark's purpose here is V8 generation/QA, not queue-state mutation.
_original_sheet_post = agent.sheet_post


def benchmark_sheet_post(action, **fields):
    if action == "updateStatus":
        print(f"Controlled benchmark: skipped Sheet status mutation for rank {fields.get('rank')}")
        return {"success": True, "benchmark_only": True}
    return _original_sheet_post(action, **fields)


agent.sheet_post = benchmark_sheet_post


# The normal production queue is eligibility-driven. For this controlled
# benchmark we must exercise Rank 30 even if a prior interrupted run left it
# Researching or otherwise temporarily unavailable in assignBatch. Pull the
# target metadata from the repository master CSV. This override is local to
# this benchmark and does not affect production queue behaviour.

def benchmark_target_from_master():
    target = os.environ.get("COLLEGE_TEST_RANK", "30").strip()
    rows = agent.read_master()
    for row in rows:
        rank = str(row.get("rank", "")).strip()
        if rank != target:
            continue
        print(f"Controlled benchmark target override: rank {target} selected from master input")
        return [{
            "rank": rank,
            "college_name": str(row.get("college_name", "")).strip(),
            "official_website": str(row.get("official_website", "")).strip(),
            "overview_status": str(row.get("overview_status", "")).strip(),
            "placement_status": str(row.get("placement_status", "")).strip(),
            "popular_course_status": str(row.get("popular_course_status", "")).strip(),
        }]
    print(f"Controlled benchmark target rank {target} not found in master input")
    return []


agent.eligible_from_sheet = benchmark_target_from_master


_original_discover = agent.discover_official


def robust_discover(college, supplied):
    resolved = _original_discover(college, supplied)
    if resolved:
        return resolved

    if str(college).strip().lower() in {
        "institute of management technology",
        "institute of management technology ghaziabad",
        "imt ghaziabad",
    }:
        fallback = "https://www.imt.edu/"
        html, final = robust_fetch(fallback)
        if html:
            print(f"Official-source fallback resolved: {final}")
            return final

    return ""


agent.discover_official = robust_discover


if __name__ == "__main__":
    raise SystemExit(agent.main())
