"""Tests for source-row-bound bibliographic triage: no external services."""
from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from scripts.validate_secondary_comparators import DEFAULT_LEDGER, validate_ledger


class SecondaryComparatorLedgerTest(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads(DEFAULT_LEDGER.read_text(encoding="utf-8"))

    def test_canonical_ledger_schema_and_independence(self):
        actual = validate_ledger(self.ledger)
        self.assertEqual(actual, {
            "decisions": 7, "source_rows": 6,
            "external_followups": 1, "zip_verified": False,
        })
        family = [r for r in self.ledger["decisions"] if r["work_family"] == "chai_humanoid_glass_wall"]
        self.assertEqual(len(family), 2)
        self.assertTrue(all(r["work_relation"] == "potential_related_work_unverified" for r in family))

    def test_duplicate_doi_does_not_count_as_independent_work(self):
        broken = deepcopy(self.ledger)
        broken["decisions"].append(deepcopy(broken["decisions"][0]))
        with self.assertRaisesRegex(ValueError, "duplicated work DOI"):
            validate_ledger(broken)

    def test_fake_source_location_for_external_followup_fails(self):
        broken = deepcopy(self.ledger)
        external = next(r for r in broken["decisions"] if r["source_kind"].startswith("external"))
        external["source_file"] = "invented.csv"
        with self.assertRaisesRegex(ValueError, "must not fabricate"):
            validate_ledger(broken)

    def test_archive_row_integrity_and_wrong_doi_rejected(self):
        single = deepcopy(self.ledger)
        single["decisions"] = [single["decisions"][0]]
        entry = single["decisions"][0]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["Paper Title", "DOI"])
        writer.writeheader()
        writer.writerow({"Paper Title": entry["title"], "DOI": entry["doi"]})
        with TemporaryDirectory() as folder:
            zip_path = Path(folder) / "mock.zip"
            with ZipFile(zip_path, "w") as z:
                z.writestr(entry["source_file"], buf.getvalue())
            with zip_path.open("rb") as stream:
                single["archive_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
            entry["source_record"] = 1
            self.assertTrue(validate_ledger(single, zip_path)["zip_verified"])
            entry["doi"] = "10.9999/wrong"
            with self.assertRaisesRegex(ValueError, "source DOI mismatch"):
                validate_ledger(single, zip_path)

    def test_missing_source_and_unsupported_evidence_level(self):
        broken = deepcopy(self.ledger)
        broken["decisions"][0]["evidence_level"] = "reproduced_independent_experiment"
        with self.assertRaisesRegex(ValueError, "unknown evidence level"):
            validate_ledger(broken)


if __name__ == "__main__":
    unittest.main()
