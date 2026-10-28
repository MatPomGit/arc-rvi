"""Tests for reviewed DOI-version linkage without unsafe automatic merging."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.reconcile_literature_versions import reconcile


SOURCE = "a" * 64


def fixtures():
    pairs = [
        ("10.1234/conf", "10.48550/arxiv.1234"),
        ("10.1234/journal", "10.48550/arxiv.5678"),
    ]
    candidates = []
    for i, doi in enumerate([x for pair in pairs for x in pair] + ["10.9999/unrelated"]):
        candidates.append({
            "candidate_id": f"id{i}", "doi": doi, "mentions": "1",
            "studies": "P03", "source_records": f"source.csv#{i+1}",
        })
    relations = []
    for i, (canonical, other) in enumerate(pairs):
        relations.append({
            "canonical_doi": canonical, "other_doi": other,
            "status": "verified_same_work" if i == 0 else "pending_publisher_relation",
            "source_urls": ["https://arxiv.org/abs/test", "https://example.org/article"],
        })
    return candidates, {"source_archive_sha256": SOURCE, "export_records": 5}, {
        "schema_version": "1.0.0", "source_archive_sha256": SOURCE,
        "relations": relations,
    }


class ReviewedWorkLinkTests(unittest.TestCase):
    def test_only_verified_link_is_joined(self):
        works, source, rel = fixtures()
        rows, receipt = reconcile(works, source, rel)
        self.assertEqual(receipt["candidate_keys"], 5)
        self.assertEqual(receipt["approved_same_work_links"], 1)
        self.assertEqual(receipt["unresolved_links"], 1)
        self.assertEqual(receipt["provisional_work_keys_after_reviewed_links"], 4)
        self.assertEqual(rows[0]["work_key"], rows[1]["work_key"])
        self.assertNotEqual(rows[2]["work_key"], rows[3]["work_key"])
        self.assertEqual(rows[4]["relation_status"], "not_reviewed")

    def test_unreviewed_or_ambiguous_relations_fail_closed(self):
        works, source, rel = fixtures()
        bad = deepcopy(rel)
        bad["relations"][1]["status"] = "verified"
        with self.assertRaises(ValueError):
            reconcile(works, source, bad)
        bad = deepcopy(rel)
        bad["relations"].append(deepcopy(bad["relations"][0]))
        with self.assertRaises(ValueError):
            reconcile(works, source, bad)
        bad = deepcopy(rel)
        bad["relations"][0]["other_doi"] = "10.1234/nonexistent"
        with self.assertRaises(ValueError):
            reconcile(works, source, bad)

    def test_source_hash_and_mentions_are_required(self):
        works, source, rel = fixtures()
        bad = deepcopy(source)
        bad["source_archive_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            reconcile(works, bad, rel)
        bad = deepcopy(source)
        bad["export_records"] = 6
        with self.assertRaises(ValueError):
            reconcile(works, bad, rel)

    def test_no_repeated_candidates(self):
        works, source, rel = fixtures()
        works[1]["candidate_id"] = works[0]["candidate_id"]
        with self.assertRaises(ValueError):
            reconcile(works, source, rel)


if __name__ == "__main__":
    unittest.main()
