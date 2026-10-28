"""Validate curated secondary literature comparator records without network access.

The ledger is a selective editorial triage, NOT a systematic screen.
An optional source ZIP verifies each CSV source-file row and its SHA-256.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

from scripts.audit_full_literature_archive import normalize_doi, normalize_title

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")
VALID_KINDS = {"secondary_csv", "external_followup_not_in_secondary_only_queue"}
VALID_LEVELS = {
    "conference_program_and_bibliographic_record",
    "bibliographic_abstract",
    "publisher_abstract",
    "publisher_abstract_and_visible_sections",
    "author_manuscript_abstract_and_bibliography",
}
VALID_STUDIES = {"P03", "P04", "P06", "P08"}
DEFAULT_LEDGER = (
    Path(__file__).resolve().parents[1]
    / "research/literature/secondary_comparator_decisions.json"
)


def validate_ledger(data: dict, archive: Path | None = None) -> dict:
    if data.get("schema_version") != 1:
        raise ValueError("unsupported ledger schema_version")
    records = data.get("decisions")
    if not isinstance(records, list) or not records:
        raise ValueError("decisions must be a nonempty list")
    archive_hash = data.get("archive_sha256")
    if not isinstance(archive_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", archive_hash):
        raise ValueError("invalid source archive hash")
    checked = set()
    csv_rows = 0
    for item in records:
        doi = item.get("doi")
        if not isinstance(doi, str) or doi != normalize_doi(doi) or not DOI_PATTERN.fullmatch(doi):
            raise ValueError("DOI must be a normalized syntactically valid string")
        if doi in checked:
            raise ValueError(f"duplicated work DOI: {doi}")
        checked.add(doi)
        if item.get("source_kind") not in VALID_KINDS:
            raise ValueError(f"unknown source kind for {doi}")
        if item.get("evidence_level") not in VALID_LEVELS:
            raise ValueError(f"unknown evidence level for {doi}")
        if not isinstance(item.get("title"), str) or not normalize_title(item["title"]):
            raise ValueError(f"missing title for {doi}")
        if not isinstance(item.get("studies"), list) or not item["studies"] or len(item["studies"]) != len(set(item["studies"])) or not set(item["studies"]) <= VALID_STUDIES:
            raise ValueError(f"invalid study mapping for {doi}")
        for field in ("primary_url", "relevance", "comparator_requirement", "claims_not_supported", "work_family", "work_relation"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"missing {field} for {doi}")
        if not item["primary_url"].startswith("https://"):
            raise ValueError(f"invalid primary_url for {doi}")
        if item["source_kind"] == "secondary_csv":
            if not isinstance(item.get("source_file"), str) or not item["source_file"].endswith(".csv"):
                raise ValueError(f"missing CSV provenance for {doi}")
            if type(item.get("source_record")) is not int or item["source_record"] < 1:
                raise ValueError(f"invalid CSV row provenance for {doi}")
            csv_rows += 1
        elif item.get("source_file") is not None or item.get("source_record") is not None:
            raise ValueError(f"external follow-up must not fabricate a CSV row: {doi}")

    if archive is not None:
        with archive.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != archive_hash:
            raise ValueError("source ZIP SHA-256 mismatch")
        with ZipFile(archive) as z:
            for item in records:
                if item["source_kind"] != "secondary_csv":
                    continue
                name = item["source_file"]
                if name not in z.namelist():
                    raise ValueError(f"source CSV missing: {name}")
                member = z.getinfo(name)
                if member.file_size > 8_000_000:
                    raise ValueError(f"source CSV exceeds safety limit: {name}")
                rows = csv.DictReader(io.StringIO(z.read(member).decode("utf-8-sig")))
                for rownum, row in enumerate(rows, 1):
                    if rownum == item["source_record"]:
                        if normalize_doi(row.get("DOI") or "") != item["doi"]:
                            raise ValueError(f"source DOI mismatch: {name}#{rownum}")
                        if normalize_title(row.get("Paper Title") or "") != normalize_title(item["title"]):
                            raise ValueError(f"source title mismatch: {name}#{rownum}")
                        break
                else:
                    raise ValueError(f"missing source data row: {name}#{item['source_record']}")
    return {"decisions": len(records), "source_rows": csv_rows, "external_followups": len(records)-csv_rows, "zip_verified": archive is not None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    data = json.loads(args.ledger.read_text(encoding="utf-8"))
    result = validate_ledger(data, args.archive)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
