"""Apply source-backed manual screening decisions to an immutable CSV inventory.

This tool never infers eligibility from article titles or numeric relevance scores.
Unreviewed items remain unreviewed. No online service is contacted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

STATUSES = {"direct_prior_art", "contextual_only", "exclude_direct_evidence"}


def apply_decisions(candidates: list[dict], inventory: dict, manifest: dict) -> tuple[list[dict], dict]:
    if manifest.get("schema_version") != "1.0.0":
        raise ValueError("unsupported screening manifest version")
    if inventory.get("source_archive_sha256") != manifest.get("source_archive_sha256"):
        raise ValueError("source archive SHA-256 mismatch")
    if len(candidates) != inventory.get("candidate_keys"):
        raise ValueError("candidate inventory count mismatch")
    by_id = {}
    for row in candidates:
        key = row.get("candidate_id", "")
        if not key or key in by_id:
            raise ValueError("missing or duplicate candidate ID")
        if not row.get("source_records"):
            raise ValueError("candidate source trace is missing")
        by_id[key] = row
    if sum(int(r["mentions"]) for r in candidates) != inventory.get("export_records"):
        raise ValueError("source mention count mismatch")

    decisions = {}
    for item in manifest.get("decisions", []):
        key = item.get("candidate_id", "")
        if key not in by_id or key in decisions:
            raise ValueError("unknown or duplicate screening candidate")
        if item.get("doi", "") != by_id[key].get("doi", ""):
            raise ValueError("DOI mismatch for screened candidate")
        if item.get("status") not in STATUSES:
            raise ValueError("unsupported manual screening status")
        evidence = item.get("evidence_urls")
        if (not isinstance(evidence, list) or not evidence
                or not all(isinstance(url, str) and url.startswith("https://") for url in evidence)):
            raise ValueError("a reviewer decision requires HTTPS evidence")
        if not item.get("rationale", "").strip() or not item.get("review_date", "").strip():
            raise ValueError("a reviewer decision requires rationale and date")
        decisions[key] = item

    output = []
    counts = Counter()
    for candidate in candidates:
        decision = decisions.get(candidate["candidate_id"])
        status = decision["status"] if decision else "not_reviewed"
        counts[status] += 1
        output.append({
            "candidate_id": candidate["candidate_id"],
            "doi": candidate["doi"],
            "title_as_exported": candidate["title"],
            "source_records": candidate["source_records"],
            "studies": candidate["studies"],
            "screening_status": status,
            "review_date": decision["review_date"] if decision else "",
            "rationale": decision["rationale"] if decision else "",
            "evidence_urls": ";".join(decision["evidence_urls"]) if decision else "",
        })
    return output, {
        "source_archive_sha256": inventory["source_archive_sha256"],
        "candidate_keys": len(candidates),
        "export_row_mentions": inventory["export_records"],
        "status_counts": dict(sorted(counts.items())),
        "reviewed_candidate_keys": len(decisions),
        "unreviewed_candidate_keys": len(candidates) - len(decisions),
        "limitation": "Decisions are source-backed topical assessments; no study eligibility or empirical finding established for unreviewed items.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--inventory-summary", type=Path, required=True)
    parser.add_argument("--decisions", type=Path,
                        default=Path("research/literature/manual_screening_decisions.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with args.candidates.open(encoding="utf-8", newline="") as f:
        candidates = list(csv.DictReader(f))
    inventory = json.loads(args.inventory_summary.read_text(encoding="utf-8"))
    manifest = json.loads(args.decisions.read_text(encoding="utf-8"))
    rows, receipt = apply_decisions(candidates, inventory, manifest)
    outputs = [args.output_dir / "manual_screening.csv",
               args.output_dir / "manual_screening_receipt.json"]
    if any(path.exists() for path in outputs):
        parser.error("output already exists; choose a new output directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with outputs[0].open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    receipt["manifest_sha256"] = hashlib.sha256(args.decisions.read_bytes()).hexdigest()
    outputs[1].write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
