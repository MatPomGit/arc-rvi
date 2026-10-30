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
            (root / "README.md").write_text("# Index\n", encoding="utf-8")
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
            self.assertTrue((destination / "index.md").exists())
            self.assertTrue((destination / "docs" / "guide.md").exists())
            self.assertEqual(
                (destination / "docs" / "assets" / "theme.css").read_text(
                    encoding="utf-8"
                ),
                css,
            )


if __name__ == "__main__":
    unittest.main()
