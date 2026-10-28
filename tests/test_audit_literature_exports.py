"""Regression tests for the offline literature export inventory."""
from __future__ import annotations

import csv
import io
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import audit_literature_exports as literature


class LiteratureExportAuditTests(unittest.TestCase):
    def test_identifier_normalization(self) -> None:
        self.assertEqual(literature.normalized_doi("https://doi.org/10.1007/ABC"), "10.1007/abc")
        self.assertEqual(literature.normalized_title("Zażółć Gęślą"), "zazolcgesla")
        self.assertEqual(literature.normalized_title("Inspection<sup>*</sup>"),
                         literature.normalized_title("Inspection*"))

    def test_exact_doi_dedup_and_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "inputs.zip"
            with ZipFile(archive, "w") as sink:
                for idx, filename in enumerate(literature.STUDIES.values(), 1):
                    body = io.StringIO()
                    w = csv.DictWriter(body, fieldnames=sorted(literature.REQUIRED))
                    w.writeheader()
                    row = {"Paper Title": f"Paper {idx}", "DOI": f"10.1234/p{idx}",
                           "Publication Year": "2025", "Author Names": "Researcher",
                           "Abstract": "Abstract text", "Paper Link": "https://example.org"}
                    if idx == 8:
                        row["DOI"] = ""
                    w.writerow(row)
                    if idx == 1:
                        w.writerow({**row, "DOI": "https://doi.org/10.1234/P1"})
                    sink.writestr(filename, body.getvalue())
            report, works, queue = literature.audit(archive)
            self.assertEqual(report["export_records"], 9)
            self.assertEqual(report["candidate_keys"], 8)
            self.assertEqual(report["duplicate_mentions_by_key"], 1)
            self.assertEqual(report["missing_fields"]["missing_doi"], 1)
            self.assertEqual(len(works), 8)
            self.assertEqual(len(queue), 1)
            self.assertEqual(sum(w["mentions"] for w in works), 9)

    def test_identifier_collision_ledger_keeps_original_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "collisions.zip"
            with ZipFile(archive, "w") as sink:
                for idx, filename in enumerate(literature.STUDIES.values(), 1):
                    body = io.StringIO()
                    writer = csv.DictWriter(body, fieldnames=sorted(literature.REQUIRED))
                    writer.writeheader()
                    record = {"Paper Title": f"Inspection Paper {idx}",
                              "DOI": f"10.1234/p{idx}", "Publication Year": "2026",
                              "Author Names": "Author", "Abstract": "Abstract",
                              "Paper Link": "https://example.org"}
                    if idx == 3:
                        record["Paper Title"] = "Inspection Paper 1"
                    writer.writerow(record)
                    if idx == 1:
                        writer.writerow({**record, "Paper Title": "Inspection Paper 1<sup>*</sup>"})
                    if idx == 2:
                        writer.writerow({**record, "Paper Title": "Another research"})
                    sink.writestr(filename, body.getvalue())
            report, _, _ = literature.audit(archive)
            conflicts = report["identifier_conflicts"]
            self.assertEqual(report["doi_with_conflicting_titles"], 1)
            self.assertEqual(report["titles_with_multiple_dois"], 1)
            self.assertEqual(len(conflicts), 2)
            self.assertTrue(all(c["review_status"] == "pending" for c in conflicts))
            self.assertTrue(all(c["source_records"] for c in conflicts))

    def test_reject_missing_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "incomplete.zip"
            with ZipFile(archive, "w") as sink:
                sink.writestr(next(iter(literature.STUDIES.values())), "Paper Title,DOI\nTest,10.1234/test\n")
            with self.assertRaises(ValueError):
                literature.audit(archive)


if __name__ == "__main__":
    unittest.main()
