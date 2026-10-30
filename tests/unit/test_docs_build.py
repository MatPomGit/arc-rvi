"""Regression for canonical MkDocs Markdown and stylesheet staging."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_docs


class DocsBuildTests(unittest.TestCase):
    def test_stages_canonical_markdown_and_theme(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs" / "assets").mkdir(parents=True)
            (root / "index.md").write_text("# Welcome\n", encoding="utf-8")
            (root / "README.md").write_text("# Full README\n", encoding="utf-8")
            (root / "AUTOPILOT_PLAN.md").write_text("# Plan\n", encoding="utf-8")
            (root / "PROJECT_STATE.yaml").write_text("version: 1\n", encoding="utf-8")
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            css = "body { color: var(--text-primary); }\n"
            (root / "docs" / "assets" / "theme.css").write_text(
                css, encoding="utf-8"
            )
            destination = root / ".build" / "mkdocs-src"
            with patch.object(build_docs, "ROOT", root):
                with patch.object(build_docs, "DEST", destination):
                    build_docs.main()
            self.assertEqual(
                (destination / "index.md").read_text(encoding="utf-8"),
                "# Welcome\n",
            )
            self.assertEqual(
                (destination / "README.md").read_text(encoding="utf-8"),
                "# Full README\n",
            )
            self.assertTrue((destination / "docs" / "guide.md").exists())
            self.assertEqual(
                (destination / "docs" / "assets" / "theme.css").read_text(
                    encoding="utf-8"
                ),
                css,
            )


    def test_native_colour_modes_do_not_conflict_with_legacy_css(self):
        root = Path(__file__).resolve().parents[2]
        configuration = (root / "mkdocs.yml").read_text(encoding="utf-8")
        css = (root / "docs" / "assets" / "theme.css").read_text(
            encoding="utf-8"
        )
        self.assertIn("  color_mode: auto", configuration)
        self.assertIn("  user_color_mode_toggle: true", configuration)
        self.assertIn("  nav_style: dark", configuration)
        self.assertIn("  - Project:\\n      - Repository README: README.md".replace(
            "\\\\n", "\\n"
        ), configuration)
        self.assertNotIn("prefers-color-scheme", css)
        self.assertNotIn(".navbar-default", css)
        self.assertIn("var(--bs-body-color)", css)
        self.assertIn("var(--bs-border-color)", css)


if __name__ == "__main__":
    unittest.main()
