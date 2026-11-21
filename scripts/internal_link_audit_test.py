import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import internal_link_audit as audit


class InternalLinkAuditNestedRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "index.html").write_text("<html></html>", encoding="utf-8")
        (self.root / "root-profile.html").write_text("<html></html>", encoding="utf-8")
        (self.root / "mba-colleges" / "iim-ahmedabad" / "fees").mkdir(parents=True)
        (self.root / "mba-colleges" / "iim-ahmedabad" / "index.html").write_text("<html></html>", encoding="utf-8")
        (self.root / "mba-colleges" / "iim-ahmedabad" / "fees" / "index.html").write_text("<html></html>", encoding="utf-8")
        (self.root / "mba-colleges" / "fees" / "index.html").parent.mkdir(parents=True, exist_ok=True)
        (self.root / "mba-colleges" / "fees" / "index.html").write_text("<html></html>", encoding="utf-8")
        (self.root / "assets").mkdir()
        (self.root / "assets" / "prospectus.pdf").write_bytes(b"test")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nested_directory_index_uses_clean_slashless_public_path(self):
        self.assertEqual(
            audit.public_url_path_for_source("mba-colleges/iim-ahmedabad/index.html"),
            "/mba-colleges/iim-ahmedabad",
        )

    def test_root_index_uses_homepage_path(self):
        self.assertEqual(audit.public_url_path_for_source("index.html"), "/")

    def test_root_relative_nested_clean_route_resolves_directory_index(self):
        self.assertEqual(
            audit.local_target("/mba-colleges/iim-ahmedabad/fees", root=self.root),
            "mba-colleges/iim-ahmedabad/fees/index.html",
        )

    def test_relative_href_resolves_against_browser_clean_route_not_disk_folder(self):
        # A slashless public route is file-like to the browser; relative fees
        # resolves to /mba-colleges/fees, not the filesystem sibling directory.
        self.assertEqual(
            audit.local_target("fees", "mba-colleges/iim-ahmedabad/index.html", root=self.root),
            "mba-colleges/fees/index.html",
        )

    def test_same_origin_absolute_link_resolves_nested_route(self):
        self.assertEqual(
            audit.local_target("https://www.collegedecoded.in/mba-colleges/iim-ahmedabad/fees", root=self.root),
            "mba-colleges/iim-ahmedabad/fees/index.html",
        )

    def test_missing_clean_route_returns_expected_file_for_broken_detection(self):
        expected = audit.local_target("/mba-colleges/iim-ahabad/mba", root=self.root)
        self.assertEqual(expected, "mba-colleges/iim-ahabad/mba.html")
        self.assertFalse((self.root / expected).is_file())

    def test_missing_asset_returns_exact_expected_path(self):
        expected = audit.local_target("/assets/missing.pdf", root=self.root)
        self.assertEqual(expected, "assets/missing.pdf")
        self.assertFalse((self.root / expected).is_file())

    def test_existing_static_asset_resolves_exact_file(self):
        self.assertEqual(
            audit.local_target("/assets/prospectus.pdf", root=self.root),
            "assets/prospectus.pdf",
        )

    def test_generated_news_index_resolves_when_build_output_exists(self):
        news_index = self.root / "news" / "index.html"
        news_index.parent.mkdir(parents=True)
        news_index.write_text("<html></html>", encoding="utf-8")
        self.assertEqual(audit.local_target("/news", root=self.root), "news/index.html")

    def test_protocol_relative_same_origin_link_resolves(self):
        self.assertEqual(
            audit.local_target("//collegedecoded.in/mba-colleges/iim-ahmedabad/fees", root=self.root),
            "mba-colleges/iim-ahmedabad/fees/index.html",
        )

    def test_protocol_relative_external_link_is_ignored(self):
        self.assertIsNone(audit.local_target("//example.com/college", root=self.root))

    def test_external_link_is_not_local(self):
        self.assertIsNone(audit.local_target("https://example.com/college"))

    def test_nested_public_collector_excludes_hidden_and_cms_source(self):
        hidden = self.root / "mba-colleges" / ".hidden" / "secret.html"
        hidden.parent.mkdir()
        hidden.write_text("x", encoding="utf-8")
        cms = self.root / "mba-colleges" / "college-cms" / "content" / "draft.html"
        cms.parent.mkdir(parents=True)
        cms.write_text("x", encoding="utf-8")
        pages = audit.collect_nested_public_pages(self.root)
        self.assertIn("mba-colleges/iim-ahmedabad/index.html", pages)
        self.assertNotIn("mba-colleges/.hidden/secret.html", pages)
        self.assertNotIn("mba-colleges/college-cms/content/draft.html", pages)

    def test_main_scans_nested_pages_and_reports_missing_local_links(self):
        (self.root / "root-profile.html").write_text(
            '<a href="/mba-colleges/iim-ahmedabad">nested route</a>'
            '<a href="/missing-root-route">missing route</a>',
            encoding="utf-8",
        )
        nested = self.root / "mba-colleges" / "iim-ahmedabad" / "index.html"
        nested.parent.mkdir(parents=True, exist_ok=True)
        nested.write_text(
            '<a href="/mba-colleges/iim-ahmedabad/fees">valid nested route</a>'
            '<a href="/mba-colleges/iim-ahabad/unknown">wrong route</a>',
            encoding="utf-8",
        )
        report_path = self.root / "audit-report.json"
        old_root, old_report = audit.ROOT, audit.REPORT
        try:
            audit.ROOT, audit.REPORT = self.root, report_path
            with redirect_stdout(io.StringIO()):
                audit.main()
            report = json.loads(report_path.read_text(encoding="utf-8"))
            summary = report["summary"]
            self.assertEqual(summary["nested_public_pages_checked"], 3)
            self.assertEqual(summary["all_public_pages_checked"], 5)
            self.assertEqual(summary["broken_local_links"], 2)
            broken_sources = {item["source"] for item in report["broken_local_links"]}
            self.assertIn("root-profile.html", broken_sources)
            self.assertIn("mba-colleges/iim-ahmedabad/index.html", broken_sources)
        finally:
            audit.ROOT, audit.REPORT = old_root, old_report


if __name__ == "__main__":
    unittest.main()
