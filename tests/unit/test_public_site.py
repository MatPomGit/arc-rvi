"""Regression tests for the generated publication boundary."""
import json
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

    def test_inline_markup_and_polish_inflections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "search").mkdir()
            index = root / "search" / "search_index.json"
            page = root / "index.html"
            def write_index(value):
                index.write_text(json.dumps({"docs": [{"text": value}]}), encoding="utf-8")

            write_index("Research")
            for markup in ("<p>ag<strong>ent</strong></p>",
                           '<p>ag<span title="Research">entem</span></p>',
                           "<p>Współpraca z agentem AI.</p>",
                           "<p>AG<em>EN</em>CI</p>"):
                with self.subTest(markup=markup):
                    page.write_text(markup, encoding="utf-8")
                    self.assertTrue(any("index.html" in p for p in audit(root)))
            page.write_text("<p>ag</p><p>ent</p><p>reagents</p>", encoding="utf-8")
            self.assertEqual(audit(root), [])
            for content in ("agentem", "ag<strong>ent</strong>", "ag<em>enci</em>"):
                with self.subTest(content=content):
                    write_index(content)
                    self.assertTrue(any("search_index.json" in p for p in audit(root)))
            write_index("<p>ag</p><p>ent</p>")
            self.assertEqual(audit(root), [])
            index.write_text(json.dumps({"docs": [{"text": "ag"}, {"text": "ent"}]}),
                             encoding="utf-8")
            self.assertEqual(audit(root), [])

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
