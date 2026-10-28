"""Conservatively reconcile *reviewed* DOI-version pairs in an ARC-RVI inventory.

This is work-identity linkage, not a claim of unique eligible research studies.
Pending links remain separate. No external calls or source-file modifications.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from scripts.audit_literature_exports import normalized_doi

REVIEWED = "verified_same_work"
PENDING = {"pending_publisher_relation", "pending_repository_relation"}


def reconcile(candidates: list[dict], inventory: dict, manifest: dict) -> tuple[list[dict], dict]:
    if manifest.get("schema_version") != "1.0.0":
        raise ValueError("unsupported relation manifest")
    if inventory.get("source_archive_sha256") != manifest.get("source_archive_sha256"):
        raise ValueError("source archive SHA-256 mismatch")
    ids = [row["candidate_id"] for row in candidates]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("candidate IDs missing or repeated")
    doi_to_id = {}
    for row in candidates:
        doi = normalized_doi(row["doi"])
        if doi:
            if doi in doi_to_id:
                raise ValueError(f"multiple candidate keys for DOI: {doi}")
            doi_to_id[doi] = row["candidate_id"]
    merges: dict[str, str] = {}
    seen: set[str] = set()
    decisions: dict[str, tuple[str, str]] = {}
    reviewed_links = 0
    pending_links = 0
    for relation in manifest["relations"]:
        canonical = relation["canonical_doi"]
        other = relation["other_doi"]
        status = relation["status"]
        if (canonical != normalized_doi(canonical) or other != normalized_doi(other)
                or canonical == other or canonical in seen or other in seen):
            raise ValueError("ambiguous, repeated or unnormalized DOI linkage")
        if canonical not in doi_to_id or other not in doi_to_id:
            raise ValueError(f"relation DOI absent from inventory: {canonical} / {other}")
        urls = relation.get("source_urls", [])
        if not (isinstance(urls, list) and len(urls) >= 2
                and all(isinstance(url, str) and url.startswith("https://") for url in urls)):
            raise ValueError("relation needs at least two external source URLs")
        seen.update((canonical, other))
        if status == REVIEWED:
            reviewed_links += 1
            merges[other] = canonical
        elif status in PENDING:
            pending_links += 1
        else:
            raise ValueError(f"unsupported relation status: {status}")
        decisions[canonical] = status, canonical
        decisions[other] = status, canonical
    output = []
    for row in candidates:
        doi = normalized_doi(row["doi"])
        status, canonical = decisions.get(doi, ("not_reviewed", ""))
        work_key = ("work:doi:" + merges.get(doi, doi)
                    if status == REVIEWED else "candidate:" + row["candidate_id"])
        output.append({
            "candidate_id": row["candidate_id"], "doi": doi,
            "work_key": work_key, "relation_status": status,
            "relation_canonical_doi": canonical,
            "studies": row["studies"], "source_records": row["source_records"],
            "mentions": row["mentions"],
        })
    grouped = {row["work_key"] for row in output}
    expected = len(candidates) - reviewed_links
    if len(grouped) != expected:
        raise ValueError("unexpected identity collapse")
    receipt = {
        "source_archive_sha256": inventory["source_archive_sha256"],
        "relation_manifest_sha256": hashlib.sha256(
            (json.dumps(manifest, sort_keys=True, ensure_ascii=False) + "\n").encode()
        ).hexdigest(),
        "candidate_keys": len(candidates),
        "approved_same_work_links": reviewed_links,
        "unresolved_links": pending_links,
        "provisional_work_keys_after_reviewed_links": len(grouped),
        "input_row_mentions": sum(int(row["mentions"]) for row in candidates),
        "limitation": "Reviewed DOI pairs share provisional work identity; no eligibility, complete version history or full-text validation inferred.",
    }
    if receipt["input_row_mentions"] != inventory["export_records"]:
        raise ValueError("candidate row-mention count does not match inventory")
    return output, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--inventory-summary", type=Path, required=True)
    parser.add_argument("--relations", type=Path,
                        default=Path("research/literature/work_version_relations.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with args.candidates.open(encoding="utf-8", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    inventory = json.loads(args.inventory_summary.read_text(encoding="utf-8"))
    manifest = json.loads(args.relations.read_text(encoding="utf-8"))
    rows, receipt = reconcile(candidates, inventory, manifest)
    outputs = (args.output_dir / "reviewed_work_links.csv",
               args.output_dir / "reconciliation_receipt.json")
    if any(path.exists() for path in outputs):
        parser.error("output already exists; select a new output directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with outputs[0].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    outputs[1].write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
