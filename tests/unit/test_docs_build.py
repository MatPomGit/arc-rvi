"""Regression for canonical MkDocs Markdown and stylesheet staging."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_docs


class DocsBuildTests(unittest.TestCase):
    def test_stages_only_manifest_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "website" / "content").mkdir(parents=True)
            (root / "website" / "content" / "index.md").write_text("# Home", encoding="utf-8")
            (root / "docs" / "assets").mkdir(parents=True)
            (root / "docs" / "guide.md").write_text("# Guide", encoding="utf-8")
            (root / "docs" / "unlisted.md").write_text("internal agent instructions", encoding="utf-8")
            (root / "docs" / "assets" / "theme.css").write_text("body {}", encoding="utf-8")
            manifest = root / "website" / "public-sources.txt"
            manifest.write_text(
                "website/content/index.md | index.md\n"
                "docs/guide.md | docs/guide.md\n"
                "docs/assets/theme.css | docs/assets/theme.css\n", encoding="utf-8"
            )
            destination = root / ".build" / "mkdocs-src"
            destination.mkdir(parents=True)
            (destination / "stale.md").write_text("old content", encoding="utf-8")
            with patch.object(build_docs, "ROOT", root), patch.object(build_docs, "DEST", destination):
                build_docs.main()
                self.assertEqual(
                    {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()},
                    {"index.md", "docs/guide.md", "docs/assets/theme.css"},
                )
                manifest.write_text(manifest.read_text() + "docs/unlisted.md | docs/unlisted.md\n")
                with self.assertRaisesRegex(ValueError, "Non-public operational"):
                    build_docs.main()
                self.assertFalse(destination.exists())

    def test_rejects_path_escape_and_internal_paths(self):
        for name in ("../outside.md", "docs/AGENTS.md", "docs/agent-workflow.md"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                build_docs.safe_relative(name)

    def test_native_colour_modes_do_not_conflict_with_legacy_css(self):
        root = Path(__file__).resolve().parents[2]
        configuration = (root / "mkdocs.yml").read_text(encoding="utf-8")
        css = (root / "docs" / "assets" / "theme.css").read_text(
            encoding="utf-8"
        )
        self.assertIn("  color_mode: auto", configuration)
        self.assertIn("  user_color_mode_toggle: true", configuration)
        self.assertIn("  nav_style: dark", configuration)
        self.assertIn("      - Research software: project-readme.md", configuration)
        self.assertNotIn("prefers-color-scheme", css)
        self.assertNotIn(".navbar-default", css)
        self.assertIn("var(--bs-body-color)", css)
        self.assertIn("var(--bs-border-color)", css)


    def test_pages_release_is_gated_by_branch_and_validation(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github" / "workflows" / "docs-pages.yml").read_text(
            encoding="utf-8"
        )
        release_gate = (
            "if: github.ref == 'refs/heads/main' && "
            "github.event_name != 'pull_request'"
        )
        self.assertEqual(workflow.count(release_gate), 3)
        self.assertIn("needs: [tests, build]", workflow)
        self.assertLess(workflow.index("python scripts/audit_public_site.py"),
                        workflow.index("actions/upload-pages-artifact@"))
        self.assertEqual(workflow.count("uses: actions/checkout@"), 3)
        self.assertEqual(workflow.count("persist-credentials: false"), 3)
        pilot = workflow.split("\n  pilot:\n", 1)[1].split("\n  build:\n", 1)[0]
        self.assertIn("needs: [tests]", pilot)
        self.assertIn("persist-credentials: false", pilot)
        self.assertIn("actions/upload-artifact@", pilot)


if __name__ == "__main__":
    unittest.main()
