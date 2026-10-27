"""Literature inventory tests verify source arithmetic, not metadata truth."""
import shutil
import tempfile
from pathlib import Path
import unittest

from scripts.audit_literature import DRAFTS, NAMES, audit, doi_from, matrix_rows, references


class LiteratureInventoryTests(unittest.TestCase):
    def test_attached_source_counts_and_mismatch_classes(self):
        report = audit()
        self.assertEqual(report["matrix_row_count"], 79)
        self.assertEqual(report["matrix_rows_with_doi"], 73)
        self.assertEqual(report["unique_matrix_doi_count"], 71)
        self.assertEqual(report["study_row_counts"],
                         {"P01": 9, "P02": 10, "P03": 10, "P04": 10,
                          "P05": 10, "P06": 10, "P07": 10, "P08": 10})
        self.assertEqual(report["citation_status_counts"],
                         {"matching_doi": 9, "matrix_doi_missing": 6,
                          "numbered_reference_doi_mismatch": 64})
        self.assertEqual(report["numbered_reference_count"], 30)
        self.assertTrue(report["reference_lists_identical"])
        self.assertFalse(report["doi_metadata_verified"])
        self.assertFalse(report["unreconciled_draft_counts"][
            "counts_independently_confirmed"])
        self.assertEqual(sorted(report["repeated_matrix_dois"].values()), [2, 2])

    def test_stable_provenance_and_distinct_bibliographic_claims(self):
        first, second = audit(), audit()
        self.assertEqual(first, second)
        self.assertEqual(len(first["sources"]), 4)
        self.assertEqual(len(set(x["sha256"] for x in first["sources"].values())), 4)
        self.assertEqual(len(set(x["numbered_references_sha256"]
                                 for x in first["sources"].values())), 1)
        self.assertEqual(len({x["paper"].rsplit(" [", 1)[0] for x in first["rows"]}), 77)

    def test_doi_canonicalization_and_missing_numbers(self):
        self.assertEqual(doi_from("DOI: 10.1007/S11263-021-01469-5."),
                         "10.1007/s11263-021-01469-5")
        self.assertIsNone(doi_from("—"))
        rows = matrix_rows(
            "## A.1 RVI-01: Sample\n"
            "| Example [3] | Person | 10.1234/example | a | b | c | d | e | f | g | h |\n",
            {1: {"doi": "10.1234/example"}})
        self.assertEqual(rows[0]["reference_status"], "reference_label_missing")
        with self.assertRaisesRegex(ValueError, "11 columns"):
            matrix_rows("## A.1 RVI-01: Sample\n| Test [1] | invalid |",
                        {1: {"doi": "10.1234/test"}})

    def test_numbered_reference_silent_relink_is_detected(self):
        src = (DRAFTS / NAMES[1]).read_text(encoding="utf-8")
        entries, _ = references(src)
        original = matrix_rows(src, entries)
        self.assertEqual(next(x for x in original if x["paper"].startswith("VPR-Bench"))[
            "reference_status"], "matching_doi")
        changed = src.replace("VPR-Bench [2]", "VPR-Bench [1]", 1)
        altered = matrix_rows(changed, entries)
        self.assertEqual(next(x for x in altered if x["paper"].startswith("VPR-Bench"))[
            "reference_status"], "numbered_reference_doi_mismatch")

    def test_missing_and_modified_source_not_miscounted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in NAMES:
                shutil.copyfile(DRAFTS / name, root / name)
            self.assertEqual(audit(root)["matrix_row_count"], 79)
            (root / NAMES[1]).unlink()
            with self.assertRaisesRegex(ValueError, "missing"):
                audit(root)


if __name__ == "__main__":
    unittest.main()
