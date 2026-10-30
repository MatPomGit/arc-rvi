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

    def test_malformed_nonempty_years_are_screening_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "year_quality.zip"
            with ZipFile(archive, "w") as sink:
                for idx, filename in enumerate(literature.STUDIES.values(), 1):
                    body = io.StringIO()
                    writer = csv.DictWriter(
                        body, fieldnames=sorted(literature.REQUIRED)
                    )
                    writer.writeheader()
                    row = {
                        "Paper Title": f"Study {idx}",
                        "DOI": f"10.1234/year{idx}",
                        "Publication Year": "2025",
                        "Author Names": "Author",
                        "Abstract": "Summary",
                        "Paper Link": "https://example.org",
                    }
                    if idx == 1:
                        writer.writerow({
                            **row, "DOI": "10.1234/mixed",
                            "Publication Year": "",
                        })
                        writer.writerow({
                            **row, "DOI": "10.1234/mixed",
                            "Publication Year": "20XX",
                        })
                        writer.writerow({
                            **row, "DOI": "10.1234/invalidonly",
                            "Paper Title": "Distinct invalid-year study",
                            "Publication Year": "2025/26",
                        })
                    else:
                        writer.writerow(row)
                    sink.writestr(filename, body.getvalue())

            report, candidates, queue = literature.audit(archive)
            self.assertEqual(report["export_records"], 10)
            self.assertEqual(report["candidate_keys"], 9)
            self.assertEqual(
                report["missing_fields"]["missing_or_invalid_year"], 3
            )
            by_doi = {record["doi"]: record for record in candidates}
            self.assertEqual(
                by_doi["10.1234/mixed"]["flags"],
                "year_invalid;year_missing",
            )
            self.assertEqual(
                by_doi["10.1234/invalidonly"]["flags"], "year_invalid"
            )
            self.assertEqual(
                len(by_doi["10.1234/mixed"]["source_records"].split(";")), 2
            )
            self.assertEqual(len(queue), 2)
            self.assertTrue(all(
                row["status"] == "provisional_doi" for row in queue
            ))
            self.assertEqual(report["screening_queue_candidates"], 2)

    def test_reject_ragged_rows_and_ambiguous_headers(self) -> None:
        cases = (
            "extra_cell", "missing_cell",
            "duplicate_header", "unnamed_header",
            "whitespace_duplicate_header", "unterminated_quote",
            "invalid_quote_suffix",
        )
        for kind in cases:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                archive = Path(tmp) / "malformed.zip"
                with ZipFile(archive, "w") as sink:
                    for idx, filename in enumerate(literature.STUDIES.values()):
                        columns = sorted(literature.REQUIRED)
                        fields = {
                            "Paper Title": f"Reference {idx}",
                            "DOI": f"10.1234/test{idx}",
                            "Publication Year": "2024",
                            "Author Names": "Author",
                            "Abstract": "Abstract",
                            "Paper Link": "https://example.org",
                        }
                        row = [fields[column] for column in columns]
                        header = columns[:]
                        if idx == 0:
                            if kind == "extra_cell":
                                row.append("surplus")
                            elif kind == "missing_cell":
                                row.pop()
                            elif kind == "duplicate_header":
                                header.append("DOI")
                                row.append("10.1234/ambiguous")
                            elif kind == "unnamed_header":
                                header.append("")
                                row.append("surplus")
                            elif kind == "whitespace_duplicate_header":
                                header.append("DOI ")
                                row.append("10.1234/ambiguous")
                        body = io.StringIO()
                        writer = csv.writer(body)
                        writer.writerow(header)
                        if idx == 0 and kind == "unterminated_quote":
                            body.write('"unfinished field')
                        elif idx == 0 and kind == "invalid_quote_suffix":
                            body.write('"bad"x,' + ",".join(row[1:]) + "\n")
                        else:
                            writer.writerow(row)
                        sink.writestr(filename, body.getvalue())
                first = next(iter(literature.STUDIES.values()))
                with self.assertRaisesRegex(ValueError, first):
                    literature.audit(archive)

    def test_blank_values_in_well_formed_csv_remain_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "valid_with_missing_fields.zip"
            with ZipFile(archive, "w") as sink:
                for idx, filename in enumerate(literature.STUDIES.values()):
                    fields = {
                        "Paper Title": f"Reference {idx}",
                        "DOI": f"10.1234/test{idx}",
                        "Publication Year": "2024",
                        "Author Names": "Author",
                        "Abstract": "" if idx == 0 else "Abstract",
                        "Paper Link": "https://example.org",
                    }
                    body = io.StringIO()
                    writer = csv.DictWriter(
                        body, fieldnames=sorted(literature.REQUIRED)
                    )
                    writer.writeheader()
                    writer.writerow(fields)
                    sink.writestr(filename, body.getvalue())
            report, candidates, _ = literature.audit(archive)
            self.assertEqual(report["export_records"], 8)
            self.assertEqual(report["missing_fields"]["missing_abstract"], 1)
            self.assertEqual(len(candidates), 8)

    def test_reject_missing_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "incomplete.zip"
            with ZipFile(archive, "w") as sink:
                sink.writestr(next(iter(literature.STUDIES.values())), "Paper Title,DOI\nTest,10.1234/test\n")
            with self.assertRaises(ValueError):
                literature.audit(archive)


if __name__ == "__main__":
    unittest.main()
