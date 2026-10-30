"""Independent negative and positive regressions for the agent document audit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_agent_docs import (
    inspect_agent_structure,
    inspect_agent_scenarios,
    inspect_user_text,
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

    def test_all_twenty_scenario_rows_are_required(self):
        rows = "\n".join(f"| {n:02} Case | Decision |" for n in range(1, 21))
        self.assertEqual(inspect_agent_scenarios(rows), [])
        self.assertNotEqual(
            inspect_agent_scenarios(rows.replace("| 14 Case | Decision |", "")),
            [],
        )

    def test_shared_account_comment_review_is_documented(self):
        root = Path(__file__).resolve().parents[2]
        sources = (
            "AGENTS.md",
            "docs/development/agent-workflow.md",
            "docs/development/testing.md",
            "docs/website.md",
        )
        for name in sources:
            with self.subTest(path=name):
                content = (root / name).read_text(encoding="utf-8")
                self.assertIn("COMMENTED", content)
                self.assertIn("APPROVED", content)
                self.assertIn("SHA", content)
        policy = (root / "docs/development/testing.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("TECHNICAL_REVIEW_PASS", policy)
        self.assertIn("GITHUB_APPROVED", policy)
        self.assertIn("stale SHA", policy)

    def test_user_document_rejects_typographic_dashes(self):
        self.assertEqual(inspect_user_text("Plain text - OK"), [])
        self.assertTrue(inspect_user_text("Unwanted \u2014 separator"))
        self.assertTrue(inspect_user_text("Unwanted \u2013 separator"))


if __name__ == "__main__":
    unittest.main()
