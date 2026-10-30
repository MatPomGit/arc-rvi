"""Independent negative and positive regressions for the agent document audit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_agent_docs import (
    inspect_agent_structure,
    inspect_links,
    inspect_version,
)


class AgentDocsAuditTests(unittest.TestCase):
    def test_local_target_and_external_link_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("Guide", encoding="utf-8")
            (root / "README.md").write_text(
                "[Guide](docs/guide.md#part) [Upstream](https://example.org/a)",
                encoding="utf-8",
            )
            self.assertEqual(inspect_links(root, ("README.md",)), [])

    def test_missing_local_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text(
                "[Missing](docs/absent.md)", encoding="utf-8"
            )
            issues = inspect_links(root, ("README.md",))
            self.assertEqual(len(issues), 1)
            self.assertIn("missing link target", issues[0])

    def test_link_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text(
                "[Outside](../outside.md)", encoding="utf-8"
            )
            issues = inspect_links(root, ("README.md",))
            self.assertEqual(len(issues), 1)
            self.assertIn("escapes repository", issues[0])

    def test_version_consistency_and_mismatch(self):
        project = '[project]\nname = "arc-rvi"\nversion = "1.22.2"\n'
        state = "repository:\n  software_version: 1.22.2\n"
        self.assertEqual(inspect_version(project, state), [])
        failures = inspect_version(
            project, state.replace("1.22.2", "1.22.0")
        )
        self.assertEqual(len(failures), 1)
        self.assertIn("differs", failures[0])

    def test_agent_structure_detects_missing_steps(self):
        problems = inspect_agent_structure(
            "## I. Zasady projektu\n## II. Procedura pracy agenta\n"
        )
        self.assertTrue(any("steps 1 through 8" in p for p in problems))
        self.assertTrue(any("100..200 lines" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
