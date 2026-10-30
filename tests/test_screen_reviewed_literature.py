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

    def test_review_date_must_be_an_actual_iso_calendar_date(self):
        candidates, receipt, manifest = fixtures()
        for invalid in (
            "2026-02-30", "2026-1-2", "2026-W44-3",
            "yesterday", "2026-10-28T14:00:00", "", None, 20261028,
        ):
            with self.subTest(value=invalid):
                bad = deepcopy(manifest)
                bad["decisions"][0]["review_date"] = invalid
                with self.assertRaises(ValueError):
                    apply_decisions(candidates, receipt, bad)

    def test_review_evidence_requires_an_https_host(self):
        candidates, receipt, manifest = fixtures()
        for invalid in (
            ["https://"], ["https:///path"], ["http://example.org/a"],
            ["https://[broken"], [42], "https://example.org/a",
            ["https:// bad.example/a"], ["https://exa mple.org/a"],
            ["https://example.org/" + chr(10) + "path"],
            ["https://example.org:invalid/a"],
            ["https://user:password@example.org/a"],
        ):
            with self.subTest(value=invalid):
                bad = deepcopy(manifest)
                bad["decisions"][0]["evidence_urls"] = invalid
                with self.assertRaises(ValueError):
                    apply_decisions(candidates, receipt, bad)

    def test_valid_calendar_date_and_https_evidence_are_preserved(self):
        candidates, receipt, manifest = fixtures()
        manifest["decisions"][0]["review_date"] = "2024-02-29"
        manifest["decisions"][0]["evidence_urls"] = [
            "https://example.org:443/study?version=2",
        ]
        rows, summary = apply_decisions(candidates, receipt, manifest)
        self.assertEqual(rows[0]["review_date"], "2024-02-29")
        self.assertEqual(
            rows[0]["evidence_urls"], "https://example.org:443/study?version=2"
        )
        self.assertEqual(summary["reviewed_candidate_keys"], 1)

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
        self.assertTrue(all(x["screening_status"] == "not_reviewed" for x in rows))


if __name__ == "__main__":
    unittest.main()
