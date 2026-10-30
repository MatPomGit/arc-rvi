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
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

STATUSES = {"direct_prior_art", "contextual_only", "exclude_direct_evidence"}
SOURCE_RECORD = re.compile(r"[^#;\s]+\.csv#[1-9]\d*")


def _valid_evidence_url(value: object) -> bool:
    """Require a parseable HTTPS URL with a host and no embedded credentials."""
    if (not isinstance(value, str) or not value
            or any(character.isspace() or ord(character) < 32
                   or ord(character) == 127 for character in value)):
        return False
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname
                or parsed.username is not None or parsed.password is not None):
            return False
        # urlsplit accepts malformed ports until the port property is read.
        parsed.port
    except ValueError:
        return False
    return True


def apply_decisions(candidates: list[dict], inventory: dict, manifest: dict) -> tuple[list[dict], dict]:
    if manifest.get("schema_version") != "1.0.0":
        raise ValueError("unsupported screening manifest version")
    if inventory.get("source_archive_sha256") != manifest.get("source_archive_sha256"):
        raise ValueError("source archive SHA-256 mismatch")
    if len(candidates) != inventory.get("candidate_keys"):
        raise ValueError("candidate inventory count mismatch")
    by_id = {}
    seen_sources = set()
    total_mentions = 0
    for row in candidates:
        key = row.get("candidate_id", "")
        if not key or key in by_id:
            raise ValueError("missing or duplicate candidate ID")
        source_records = row.get("source_records")
        try:
            mentions = int(row["mentions"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid source mention count") from error
        if not isinstance(source_records, str) or mentions < 1:
            raise ValueError("candidate source trace is missing or invalid")
        references = source_records.split(";")
        if (len(references) != mentions
                or len(set(references)) != len(references)
                or any(not SOURCE_RECORD.fullmatch(ref) or ref in seen_sources
                       for ref in references)):
            raise ValueError("invalid, missing or duplicate source row reference")
        seen_sources.update(references)
        total_mentions += mentions
        by_id[key] = row
    if total_mentions != inventory.get("export_records"):
        raise ValueError("source mention count mismatch")

    items = manifest.get("decisions")
    if not isinstance(items, list):
        raise ValueError("screening decisions must be an explicit list")
    decisions = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("screening decision must be an object")
        key = item.get("candidate_id", "")
        if key not in by_id or key in decisions:
            raise ValueError("unknown or duplicate screening candidate")
        if item.get("doi", "") != by_id[key].get("doi", ""):
            raise ValueError("DOI mismatch for screened candidate")
        if item.get("status") not in STATUSES:
            raise ValueError("unsupported manual screening status")
        evidence = item.get("evidence_urls")
        if (not isinstance(evidence, list) or not evidence
                or not all(_valid_evidence_url(url) for url in evidence)):
            raise ValueError("a reviewer decision requires HTTPS evidence")
        rationale = item.get("rationale")
        review_date = item.get("review_date")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("a reviewer decision requires a rationale")
        if not isinstance(review_date, str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}", review_date):
            raise ValueError("a reviewer decision requires an ISO review date")
        try:
            date.fromisoformat(review_date)
        except ValueError as error:
            raise ValueError("invalid calendar review date") from error
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
