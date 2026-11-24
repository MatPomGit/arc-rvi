"""Regression tests for the generated publication boundary."""
from pathlib import Path
import tempfile
import unittest

from scripts.audit_public_site import audit


class PublicSiteTests(unittest.TestCase):
    def test_rendered_content_and_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "search").mkdir()
            index = root / "search" / "search_index.json"
            index.write_text('{"docs":[{"title":"Research","text":"Results"}]}', encoding="utf-8")
            page = root / "index.html"
            page.write_text("<h1>Research</h1><script>const agent = 1;</script>", encoding="utf-8")
            self.assertEqual(audit(root), [])
            page.write_text('<a href="docs/%61gent-workflow/">Guide</a>', encoding="utf-8")
            self.assertTrue(any("index.html" in p for p in audit(root)))
            page.write_text("<p>agent&#115;</p>", encoding="utf-8")
            self.assertTrue(any("index.html" in p for p in audit(root)))
            page.write_text("<h1>Research</h1>", encoding="utf-8")
            index.write_text('{"docs":[{"title":"Research","text":"agent instructions"}]}', encoding="utf-8")
            self.assertTrue(any("search_index.json" in p for p in audit(root)))

    def test_stale_internal_route_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<h1>Research</h1>", encoding="utf-8")
            stale = root / "docs" / "development" / "testing"
            stale.mkdir(parents=True)
            (stale / "index.html").write_text("<h1>Guide</h1>", encoding="utf-8")
            self.assertTrue(any("Non-public output path" in p for p in audit(root)))


if __name__ == "__main__":
    unittest.main()
