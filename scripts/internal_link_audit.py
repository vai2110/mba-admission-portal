import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "internal-link-audit.json"
EXCLUDED = {
    "404.html", "content-audit.html", "college-page-audit-dashboard.html",
    "github-direct-edit-test.html", "irma-deploy-trigger.html"
}
BENCHMARKS = {"iim-ahmedabad.html", "sibm-pune.html"}
HELPER_PAGES = {
    "welingkar-mumbai-links.html",
    "welingkar-mumbai-programmes-note.html",
    "welingkar-mumbai-programmes.html",
}


def local_target(href: str):
    href = href.strip()
    if not href or href.startswith(("#", "http://", "https://", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urlsplit(href)
    path = parsed.path
    if not path:
        return None
    target = (ROOT / path.lstrip("/")) if path.startswith("/") else None
    if target is None:
        target = (ROOT / path).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return None
    return target.relative_to(ROOT).as_posix().split("#", 1)[0].split("?", 1)[0]


def page_role(name: str):
    stem = Path(name).stem
    if stem.endswith("-placements"):
        return "placement"
    return "programme"


def build_clusters(pages):
    names = set(pages)
    cluster_pages = names - HELPER_PAGES
    clusters = {}
    for placement in sorted(n for n in cluster_pages if n.endswith("-placements.html")):
        base = placement[:-len("-placements.html")] + ".html"
        if base not in cluster_pages:
            continue
        programme = []
        prefix = base[:-5]
        for name in cluster_pages:
            if name == base or name == placement:
                continue
            if name.startswith(prefix + "-"):
                programme.append(name)
        clusters[base] = {"overview": base, "placement": placement, "programmes": sorted(programme)}
    return clusters


def main():
    pages = sorted(p.name for p in ROOT.glob("*.html") if p.name not in EXCLUDED)
    page_set = set(pages)
    outgoing = defaultdict(list)
    broken = []
    benchmark_broken = []
    href_count = Counter()

    for name in pages:
        soup = BeautifulSoup((ROOT / name).read_text(encoding="utf-8"), "html.parser")
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            target = local_target(href)
            if target is None:
                continue
            href_count[name] += 1
            outgoing[name].append(target)
            if target not in page_set:
                item = {"source": name, "href": href, "target": target}
                if name in BENCHMARKS or any(name == b for b in BENCHMARKS):
                    benchmark_broken.append(item)
                else:
                    broken.append(item)

    incoming = Counter(t for targets in outgoing.values() for t in targets if t in page_set)
    clusters = build_clusters(pages)
    cluster_results = []
    missing_reciprocal = []

    for overview, cluster in clusters.items():
        members = [cluster["overview"], cluster["placement"], *cluster["programmes"]]
        members = [m for m in members if m in page_set]
        for source in members:
            targets = set(outgoing.get(source, []))
            expected = []
            if source == cluster["overview"]:
                expected = [cluster["placement"], *cluster["programmes"]]
            elif source == cluster["placement"]:
                expected = [cluster["overview"], *cluster["programmes"]]
            else:
                expected = [cluster["overview"], cluster["placement"]]
            missing = [x for x in expected if x in page_set and x not in targets]
            if missing:
                missing_reciprocal.append({"source": source, "missing": missing})
        cluster_results.append({
            "overview": cluster["overview"],
            "placement": cluster["placement"],
            "programme_count": len(cluster["programmes"]),
            "programmes": cluster["programmes"],
        })

    orphan_candidates = [
        {"page": p, "role": page_role(p), "incoming_internal_links": incoming[p]}
        for p in pages
        if incoming[p] == 0 and p not in BENCHMARKS and p not in HELPER_PAGES
    ]

    role_counts = Counter()
    for p in pages:
        if p.endswith("-placements.html"):
            role_counts["placement"] += 1
        elif any(x in p for x in ("-mba", "-pgdm", "-btech", "-bba", "-bca", "-bcom", "-pgp", "-epgp", "-executive", "-mms")):
            role_counts["programme"] += 1
        else:
            role_counts["overview_or_hub"] += 1

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Root-level HTML portal pages; benchmark pages are audited but never modified by this workflow.",
        "summary": {
            "pages_checked": len(pages),
            "pages_with_internal_links": sum(1 for p in pages if outgoing.get(p)),
            "broken_local_links": len(broken),
            "benchmark_legacy_broken_links": len(benchmark_broken),
            "college_clusters_detected": len(clusters),
            "cluster_reciprocal_gaps": len(missing_reciprocal),
            "zero_incoming_pages": len(orphan_candidates),
            "role_counts": dict(role_counts),
        },
        "college_clusters": cluster_results,
        "reciprocal_link_gaps": missing_reciprocal,
        "broken_local_links": broken,
        "benchmark_legacy_broken_links": benchmark_broken,
        "zero_incoming_pages": orphan_candidates,
        "incoming_link_counts": dict(sorted(incoming.items())),
        "outgoing_internal_link_counts": dict(sorted(href_count.items())),
        "benchmarks": sorted(BENCHMARKS),
        "helper_pages_excluded_from_clusters": sorted(HELPER_PAGES),
        "rules": [
            "Overview pages should link to their placement page and every existing dedicated programme page.",
            "Programme pages should link back to the overview and placement page.",
            "Placement pages should link back to the overview and existing programme pages.",
            "Missing pages are not created by this audit; only existing destinations are evaluated.",
            "Benchmark pages are never modified by the Phase 3 automation.",
            "Welingkar helper/hub pages are excluded from reciprocal college clusters because they are navigation utilities, not dedicated programme pages.",
            "Broken links originating from benchmark pages are reported separately and are never modified by the Phase 3 automation."
        ]
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if broken:
        print("BROKEN LOCAL LINKS:")
        for item in broken:
            print(f"- {item['source']} -> {item['href']}")
    if benchmark_broken:
        print("BENCHMARK LEGACY BROKEN LINKS (NOT MODIFIED):")
        for item in benchmark_broken:
            print(f"- {item['source']} -> {item['href']}")


if __name__ == "__main__":
    main()
