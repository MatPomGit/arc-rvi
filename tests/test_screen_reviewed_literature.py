"""Offline regression tests for manual, source-backed literature screening."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.screen_reviewed_literature import apply_decisions


def fixtures():
    candidates = [
        {"candidate_id": "id1", "doi": "10.1234/first", "title": "One",
         "source_records": "a.csv#1", "studies": "P01", "mentions": "2"},
        {"candidate_id": "id2", "doi": "10.1234/second", "title": "Two",
         "source_records": "b.csv#1", "studies": "P02", "mentions": "1"},
    ]
    inventory = {"source_archive_sha256": "a" * 64,
                 "candidate_keys": 2, "export_records": 3}
    decisions = {
        "schema_version": "1.0.0", "source_archive_sha256": "a" * 64,
        "decisions": [{"candidate_id": "id1", "doi": "10.1234/first",
                       "status": "exclude_direct_evidence", "review_date": "2026-10-28",
                       "rationale": "Source shows unrelated topic",
                       "evidence_urls": ["https://example.org/first"]}],
    }
    return candidates, inventory, decisions


class ManualScreeningTests(unittest.TestCase):
    def test_manual_only_and_unchanged_mention_count(self):
        candidates, receipt, manifest = fixtures()
        rows, result = apply_decisions(candidates, receipt, manifest)
        self.assertEqual(result["status_counts"], {"exclude_direct_evidence": 1,
                                                  "not_reviewed": 1})
        self.assertEqual(result["export_row_mentions"], 3)
        self.assertEqual(rows[0]["source_records"], "a.csv#1")
        self.assertEqual(rows[1]["rationale"], "")
        self.assertEqual(rows[1]["screening_status"], "not_reviewed")

    def test_conflicting_reviewed_items_rejected(self):
        candidates, receipt, manifest = fixtures()
        bad = deepcopy(manifest)
        bad["decisions"].append(deepcopy(bad["decisions"][0]))
        with self.assertRaises(ValueError):
            apply_decisions(candidates, receipt, bad)
        for key, value in [("candidate_id", "unknown"), ("doi", "10.9999/other")]:
            bad = deepcopy(manifest)
            bad["decisions"][0][key] = value
            with self.assertRaises(ValueError):
                apply_decisions(candidates, receipt, bad)

    def test_invalid_status_and_missing_evidence_rejected(self):
        candidates, receipt, manifest = fixtures()
        for key, value in [("status", "included"), ("evidence_urls", []),
                           ("rationale", ""), ("review_date", "")]:
            bad = deepcopy(manifest)
            bad["decisions"][0][key] = value
            with self.assertRaises(ValueError):
                apply_decisions(candidates, receipt, bad)

    def test_source_provenance_and_missing_rows_rejected(self):
        candidates, receipt, manifest = fixtures()
        for key, value in [("source_archive_sha256", "b" * 64),
                           ("candidate_keys", 3), ("export_records", 100)]:
            bad = deepcopy(receipt)
            bad[key] = value
            with self.assertRaises(ValueError):
                apply_decisions(candidates, bad, manifest)
        bad = deepcopy(candidates)
        bad[1]["candidate_id"] = "id1"
        with self.assertRaises(ValueError):
            apply_decisions(bad, receipt, manifest)

    def test_no_rules_do_not_imply_screened(self):
        candidates, receipt, manifest = fixtures()
        manifest["decisions"] = []
        rows, result = apply_decisions(candidates, receipt, manifest)
        self.assertEqual(result["reviewed_candidate_keys"], 0)
        self.assertTrue(all(x["screening_status"] == "not_reviewed" for x in rows)


if __name__ == "__main__":
    unittest.main()
