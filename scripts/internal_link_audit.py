# Sitewide SEO gate: internal links must resolve and important pages remain discoverable.
import json
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

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
# Audit nested migration-preview pages, but keep CMS source and other generated
# directories out of this public-route scan. The root-page cluster/orphan logic
# remains intentionally limited to legacy root routes.
NESTED_PUBLIC_ROOTS = ("mba-colleges",)
NESTED_IGNORED_DIRS = {".git", ".vercel", "node_modules", "college-cms", "tests", "scripts"}
OWN_HOSTS = {"collegedecoded.in", "www.collegedecoded.in"}


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value is not None:
                self.hrefs.append(value)
                break


def extract_hrefs(html: str):
    parser = AnchorParser()
    parser.feed(html)
    parser.close()
    return parser.hrefs


def public_url_path_for_source(source_name: str):
    """Return the browser-visible clean path for a source HTML file."""
    source = Path(str(source_name).replace("\\", "/"))
    if source.name.lower() == "index.html":
        return "/" if source.parent == Path(".") else "/" + source.parent.as_posix().rstrip("/")
    return "/" + source.with_suffix("").as_posix().lstrip("/")


def collect_root_pages(root=ROOT):
    return sorted(p.name for p in root.glob("*.html") if p.name not in EXCLUDED)


def collect_nested_public_pages(root=ROOT):
    """Collect HTML pages only under explicitly allowlisted public route roots."""
    pages = []
    root_resolved = root.resolve()
    for public_root in NESTED_PUBLIC_ROOTS:
        candidate_root = root / public_root
        if candidate_root.is_symlink() or not candidate_root.is_dir():
            continue
        for candidate in candidate_root.rglob("*.html"):
            if candidate.is_symlink() or not candidate.is_file():
                continue
            relative = candidate.relative_to(root).as_posix()
            parts = Path(relative).parts
            if any(part.startswith(".") or part in NESTED_IGNORED_DIRS for part in parts[:-1]):
                continue
            if candidate.name in EXCLUDED:
                continue
            try:
                resolved = candidate.resolve()
                if resolved != root_resolved and not resolved.is_relative_to(root_resolved):
                    continue
            except (OSError, ValueError):
                continue
            pages.append(relative)
    return sorted(set(pages))


def collect_audit_pages(root=ROOT):
    return sorted(set(collect_root_pages(root)) | set(collect_nested_public_pages(root)))


def local_target(href: str, source_name: str = None, root=ROOT):
    """Resolve a local href to its source path, or its expected path if missing.

    Resolving relative hrefs against the source's public URL (rather than its
    filesystem directory) mirrors browser URL behavior for clean, slashless routes.
    Returning an expected target for missing local files allows the audit to flag
    broken links instead of silently skipping them.
    """
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urlsplit(href)
    if parsed.netloc:
        # Accept same-origin protocol-relative links, but ignore other hosts and
        # non-HTTP schemes. Protocol-relative own-domain links are still local.
        if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
            return None
        if (parsed.netloc or "").lower() not in OWN_HOSTS:
            return None
        path = parsed.path or "/"
    elif parsed.scheme:
        return None
    else:
        path = parsed.path or ""
    if not path:
        return None

    if path.startswith("/"):
        resolved_path = path
    elif source_name:
        resolved_path = urlsplit(urljoin(public_url_path_for_source(source_name), path)).path
    else:
        resolved_path = "/" + path.lstrip("/")

    raw = resolved_path.lstrip("/").rstrip("/")
    if not raw:
        return "index.html"
    # Avoid returning paths outside the site root even if a malformed href was supplied.
    parts = Path(raw).parts
    if any(part in {"..", "."} for part in parts):
        return None

    if raw.lower().endswith(".html"):
        candidates = [raw]
    elif Path(raw).suffix:
        candidates = [raw]  # asset (PDF, image, CSS, etc.)
    else:
        candidates = [raw + ".html", raw + "/index.html", raw]

    for candidate in candidates:
        target = root / candidate
        try:
            resolved = target.resolve()
            root_resolved = root.resolve()
            if resolved != root_resolved and not resolved.is_relative_to(root_resolved):
                continue
        except (OSError, ValueError):
            continue
        if target.is_file():
            return target.relative_to(root).as_posix()
    # Keep the preferred route candidate when it is missing so callers can report it.
    return candidates[0]


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
    pages = collect_root_pages(ROOT)
    nested_pages = collect_nested_public_pages(ROOT)
    audit_pages = sorted(set(pages) | set(nested_pages))
    page_set = set(pages)
    audit_page_set = set(audit_pages)
    outgoing = defaultdict(list)
    broken = []
    benchmark_broken = []
    href_count = Counter()
    redirecting_internal_links = []

    for name in audit_pages:
        html = (ROOT / name).read_text(encoding="utf-8")
        for href in extract_hrefs(html):
            href = href.strip()
            target = local_target(href, source_name=name, root=ROOT)
            if target is None:
                continue
            href_count[name] += 1
            outgoing[name].append(target)
            parsed = urlsplit(href)
            raw_path = parsed.path or ""
            is_own_domain = (
                parsed.scheme in {"http", "https"}
                and (parsed.netloc or "").lower() in OWN_HOSTS
            )
            if (raw_path.lower().endswith(".html") and not parsed.query and
                    (not parsed.scheme or is_own_domain) and (ROOT / target).is_file()):
                clean_path = public_url_path_for_source(target)
                redirecting_internal_links.append({
                    "source": name, "href": href, "target": clean_path
                })
            # Broken detection now operates on the expected target returned by
            # local_target, including missing clean routes and local assets.
            if target not in audit_page_set and not (ROOT / target).is_file():
                item = {"source": name, "href": href, "target": target}
                if name in BENCHMARKS:
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
        "scope": "Root-level HTML portal pages plus allowlisted nested public-route pages; cluster/orphan analysis remains root-level only.",
        "summary": {
            "pages_checked": len(pages),
            "root_pages_checked": len(pages),
            "nested_public_pages_checked": len(nested_pages),
            "all_public_pages_checked": len(audit_pages),
            "pages_with_internal_links": sum(1 for p in audit_pages if outgoing.get(p)),
            "broken_local_links": len(broken),
            "redirecting_internal_links": len(redirecting_internal_links),
            "benchmark_legacy_broken_links": len(benchmark_broken),
            "college_clusters_detected": len(clusters),
            "cluster_reciprocal_gaps": len(missing_reciprocal),
            "zero_incoming_pages": len(orphan_candidates),
            "role_counts": dict(role_counts),
        },
        "college_clusters": cluster_results,
        "reciprocal_link_gaps": missing_reciprocal,
        "broken_local_links": broken,
        "redirecting_internal_links": redirecting_internal_links,
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
            "Broken links originating from benchmark pages are reported separately and are never modified by the Phase 3 automation.",
            "Nested public-route pages are audited for local link resolution; cluster and orphan calculations intentionally remain root-level.",
        ]
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if broken:
        print("BROKEN LOCAL LINKS:")
        for item in broken:
            print(f"- {item['source']} -> {item['href']} (expected target: {item['target']})")
    if benchmark_broken:
        print("BENCHMARK LEGACY BROKEN LINKS (NOT MODIFIED):")
        for item in benchmark_broken:
            print(f"- {item['source']} -> {item['href']} (expected target: {item['target']})")


if __name__ == "__main__":
    main()
