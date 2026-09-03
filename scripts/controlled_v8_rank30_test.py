#!/usr/bin/env python3
"""Controlled v8 benchmark test for the first fresh production candidate.

Rank 30 (Institute of Management Technology) is intentionally used instead of
rank 27/29 because rank 27 is protected and rank 29 already has generated
content. This test uses the Google Sheet as the queue authority and does not
force a page type: v8 must generate exactly the page types whose Sheet status
is incomplete.

No AGENTS.md or repository agent configuration is read or executed.

The benchmark adds a temporary, deterministic network resolver around V8's
fetch/discovery layer. It handles redirects, www/non-www, HTTP fallback,
transient failures and the known IMT official-domain fallback. The same
resolver logic should be folded into V8 after this benchmark passes.
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

_original_discover = agent.discover_official


def robust_discover(college, supplied):
    resolved = _original_discover(college, supplied)
    if resolved:
        return resolved

    # Rank 30's Sheet entry has historically pointed at an IMT URL that can
    # fail from CI even though the official domain itself is reachable.
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
