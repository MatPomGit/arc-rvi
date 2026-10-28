"""Standard-library regression tests for unscreened secondary bibliography exports."""
from __future__ import annotations

import csv
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from scripts.audit_full_literature_archive import (
    FINAL_EXPORTS,
    audit,
    normalize_doi,
    normalize_title,
)


def csv_body(rows):
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=("Paper Title", "DOI", "Publication Year", "Paper Link", "Relevant Excerpt"),
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


class FullLiteratureArchiveAuditTest(unittest.TestCase):
    def test_secondary_candidate_not_promoted_to_verified_work(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "sample.zip"
            with ZipFile(source, "w") as dest:
                for name in FINAL_EXPORTS:
                    dest.writestr(name, csv_body([{
                        "Paper Title": "Shared <sup>2</sup>",
                        "DOI": "https://doi.org/10.1111/shared",
                        "Publication Year": "2024",
                        "Paper Link": "",
                    }]))
                dest.writestr("scispace_fulltext_extra.csv", csv_body([
                    {
                        "Paper Title": "Shared 2", "DOI": "10.1111/shared",
                        "Publication Year": "2024", "Paper Link": "",
                        "Relevant Excerpt": "excerpt",
                    },
                    {
                        "Paper Title": "New paper", "DOI": "DOI:10.9999/new",
                        "Publication Year": "2025", "Paper Link": "",
                        "Relevant Excerpt": "unverified exported text",
                    },
                ]))
            summary, queue = audit(source)
        self.assertEqual(summary["final_row_mentions"], 8)
        self.assertEqual(summary["secondary_row_mentions"], 2)
        self.assertEqual(summary["secondary_doi_strings_not_in_final"], 1)
        self.assertEqual(summary["secondary_normalized_titles_not_in_final"], 1)
        self.assertEqual(summary["fulltext_named_csv_excerpt_rows"], 2)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["doi"], "10.9999/new")

    def test_normalization(self):
        self.assertEqual(normalize_doi("https://doi.org/10.1234/ABC"), "10.1234/abc")
        self.assertEqual(normalize_title("Robot <sup>2</sup>"), "robot2")

    def test_missing_final_export_rejected(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "incomplete.zip"
            with ZipFile(source, "w") as dest:
                dest.writestr("misc.csv", csv_body([]))
            with self.assertRaisesRegex(ValueError, "missing final exports"):
                audit(source)


if __name__ == "__main__":
    unittest.main()
