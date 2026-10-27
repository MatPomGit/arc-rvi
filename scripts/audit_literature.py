"""Reproducible offline bibliography/numbering audit of supplied ARC-RVI drafts.

Counts describe *source rows*, not an independently screened literature set.
DOI matching here is string equality, never publisher metadata verification.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "research" / "literature" / "source_drafts"
NAMES = (
    "ARC_RVI_Literature_Review.md",
    "ARC_RVI_Literature_Evidence_Matrices.md",
    "ARC_RVI_Gap_Analysis_Publication_Strategy.md",
    "ARC_RVI_Hypotheses_Experimental_Recommendations.md",
)
DOI = re.compile(r"\b10\.\d{4,9}/[^\s|,;>\]]+", re.IGNORECASE)
STUDY = re.compile(r"^## A\.\d+ RVI-(0[1-8]):")
REFERENCE = re.compile(r"^\[(\d{1,3})\]\s*(.+)$")


def doi_from(text: str) -> str | None:
    match = DOI.search(text)
    return match.group(0).rstrip(".\"'").lower() if match else None


def references(text: str) -> tuple[dict[int, dict], str]:
    pieces = text.split("\n## References\n")
    if len(pieces) != 2:
        raise ValueError("expected exactly one bibliography block")
    entries = {}
    for line in pieces[1].splitlines():
        match = REFERENCE.match(line)
        if match:
            number, entry = int(match.group(1)), match.group(2)
            if number in entries:
                raise ValueError("duplicate bibliography label")
            entries[number] = {"doi": doi_from(entry), "entry": entry}
    if not entries:
        raise ValueError("bibliography contains no entries")
    return entries, sha256(pieces[1].encode("utf-8")).hexdigest()


def matrix_rows(text: str, bibliography: dict[int, dict]) -> list[dict]:
    study = None
    output = []
    for line_number, line in enumerate(text.splitlines(), 1):
        match = STUDY.match(line)
        if match:
            study = "P" + match.group(1)
            continue
        if line.startswith("## References"):
            study = None
        if study is None or not line.startswith("| "):
            continue
        if line.startswith("| Paper |") or re.match(r"^\|\s*-{2}", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 11:
            raise ValueError(f"expected 11 columns at line {line_number}")
        citation = re.search(r"\[(\d{1,3})\]$", cells[0])
        if not citation:
            raise ValueError(f"missing bracket citation at line {line_number}")
        number = int(citation.group(1))
        if number not in bibliography:
            status = "reference_label_missing"
        elif cells[2] in ("—", "-", ""):
            status = "matrix_doi_missing"
        else:
            cited = doi_from(cells[2])
            if not cited:
                raise ValueError(f"malformed DOI cell at line {line_number}")
            status = ("matching_doi" if cited == bibliography[number]["doi"]
                      else "numbered_reference_doi_mismatch")
        output.append({
            "study": study,
            "matrix_line": line_number,
            "paper": cells[0],
            "citation_label": number,
            "matrix_doi": doi_from(cells[2]),
            "numbered_reference_doi": bibliography.get(number, {}).get("doi"),
            "reference_status": status,
            "metadata_verified": False,
        })
    if not output:
        raise ValueError("no evidence matrix rows found")
    return output


def audit(root: Path = DRAFTS) -> dict:
    """Make content-addressed source inventory with no network or side effects."""
    paths = [root / name for name in NAMES]
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise ValueError("missing or symlinked literature source")
    original = {name: (root / name).read_bytes() for name in NAMES}
    decoded = {name: raw.decode("utf-8") for name, raw in original.items()}
    blocks = {name: references(source) for name, source in decoded.items()}
    # Bibliography is identical in the four sources; record any divergence,
    # but never silently pretend references were independently screened.
    bibliography, ref_hash = blocks[NAMES[1]]
    rows = matrix_rows(decoded[NAMES[1]], bibliography)
    status = Counter(record["reference_status"] for record in rows)
    counts = Counter(record["study"] for record in rows)
    unique_doi = {record["matrix_doi"] for record in rows
                  if record["matrix_doi"] is not None}
    appearances = Counter(record["matrix_doi"] for record in rows
                          if record["matrix_doi"] is not None)
    return {
        "schema_version": "1.0.0",
        "audit_scope": "supplied_draft_rows_only_not_systematic_review",
        "doi_metadata_verified": False,
        "sources": {
            name: {
                "sha256": sha256(original[name]).hexdigest(),
                "numbered_reference_count": len(blocks[name][0]),
                "numbered_references_sha256": blocks[name][1],
            }
            for name in NAMES
        },
        "reference_lists_identical": all(
            value[1] == ref_hash for value in blocks.values()),
        "matrix_row_count": len(rows),
        "study_row_counts": dict(sorted(counts.items())),
        "matrix_rows_with_doi": sum(record["matrix_doi"] is not None
                                    for record in rows),
        "unique_matrix_doi_count": len(unique_doi),
        "repeated_matrix_dois": dict(sorted(
            (doi, n) for doi, n in appearances.items() if n > 1)),
        "numbered_reference_count": len(bibliography),
        "citation_status_counts": dict(sorted(status.items())),
        "unreconciled_draft_counts": {
            "narrative_claimed_unique_records": 1908,
            "gap_analysis_claimed_analyzed_records": 240,
            "screening_export_available": False,
            "counts_independently_confirmed": False,
        },
        "rows": rows,
    }



VERIFIED = ROOT / "research" / "literature" / "verified_doi_metadata.json"
VERIFIED_FIELDS = {
    "doi", "title", "first_author", "year", "venue", "source_url",
    "source_kind", "relevance", "aliases",
}


def _verified_metadata(path: Path) -> tuple[dict[str, dict], dict[str, str], str]:
    """Validate curated metadata, including documented DOI typo aliases."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing or symlinked verified metadata")
    raw = path.read_bytes()
    document = json.loads(raw.decode("utf-8"))
    if (not isinstance(document, dict)
            or set(document) != {"schema_version", "verification_date",
                                 "verification_scope", "records"}
            or document["schema_version"] != "1.0.0"
            or document["verification_scope"] !=
            "publisher_or_institutional_metadata_only_no_full_article_claim_verification"
            or not isinstance(document["verification_date"], str)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",
                                document["verification_date"])):
        raise ValueError("invalid verified metadata manifest")
    from datetime import date
    try:
        date.fromisoformat(document["verification_date"])
    except ValueError as exc:
        raise ValueError("invalid verification date") from exc
    values = document["records"]
    if not isinstance(values, list) or not 1 <= len(values) <= 200:
        raise ValueError("invalid verified record count")
    accepted: dict[str, dict] = {}
    aliases: dict[str, str] = {}
    for record in values:
        if not isinstance(record, dict) or set(record) != VERIFIED_FIELDS:
            raise ValueError("unexpected reviewed metadata fields")
        raw_doi = record["doi"]
        if (not isinstance(raw_doi, str) or doi_from(raw_doi) != raw_doi
                or raw_doi in accepted or raw_doi in aliases):
            raise ValueError("noncanonical or duplicate reviewed DOI")
        if (not isinstance(record["title"], str) or not record["title"].strip()
                or not isinstance(record["venue"], str) or not record["venue"].strip()
                or not isinstance(record["relevance"], str)
                or not record["relevance"].strip()
                or record["source_kind"] not in
                ("publisher", "institutional_repository", "bibliographic_index")
                or not isinstance(record["source_url"], str)
                or not record["source_url"].startswith("https://")
                or " " in record["source_url"]
                or type(record["year"]) is not int
                or not 1900 <= record["year"] <= 2026
                or (record["first_author"] is not None
                    and (not isinstance(record["first_author"], str)
                         or not record["first_author"].strip()))
                or not isinstance(record["aliases"], list)):
            raise ValueError("invalid reviewed publication metadata")
        accepted[raw_doi] = record
        for alias in record["aliases"]:
            if (not isinstance(alias, str) or doi_from(alias) != alias
                    or alias == raw_doi or alias in accepted or alias in aliases):
                raise ValueError("ambiguous or invalid DOI alias")
            aliases[alias] = raw_doi
    if set(aliases).intersection(accepted):
        raise ValueError("reviewed alias collides with canonical DOI")
    return accepted, aliases, sha256(raw).hexdigest()


def catalog(root: Path = DRAFTS, verified_path: Path = VERIFIED) -> dict:
    """Stable DOI-keyed mention groups without changing the archived drafts.

    DOI text establishes an *identity candidate*, not proof of metadata correctness.
    DOI-free items use local provisional IDs until a verified identifier exists.
    """
    source = audit(root)
    reviewed, aliases, review_sha = _verified_metadata(verified_path)
    groups: dict[str, dict] = {}
    for record in source["rows"]:
        raw_doi = record["matrix_doi"]
        resolved = aliases.get(raw_doi, raw_doi) if raw_doi else None
        if resolved is None:
            # A local slug is explicitly provisional; no DOI is inferred.
            raw_title = record["paper"].rsplit(" [", 1)[0]
            slug = re.sub(r"[^a-z0-9]+", "-", raw_title.lower()).strip("-")
            identity = f"unresolved:{record['study'].lower()}:{slug}"
        else:
            identity = "doi:" + resolved
        verified_record = reviewed.get(resolved) if resolved else None
        if identity not in groups:
            groups[identity] = {
                "key": identity,
                "canonical_doi": resolved,
                "metadata_status": (
                    "reviewed_metadata" if verified_record else
                    "unresolved_no_doi" if resolved is None else
                    "draft_doi_unverified"),
                "verified_metadata": (
                    {key: value for key, value in verified_record.items()
                     if key != "aliases"} if verified_record else None),
                "mentions": [],
            }
        groups[identity]["mentions"].append({
            "study": record["study"],
            "matrix_line": record["matrix_line"],
            "draft_paper": record["paper"],
            "matrix_doi": raw_doi,
            "reference_label": record["citation_label"],
            "source_reference_status": record["reference_status"],
            "resolution": (
                "curated_doi_typo_alias" if raw_doi in aliases else
                "raw_doi_only" if resolved else
                "identifier_missing"),
        })
    unseen = sorted(set(reviewed) - {
        item["canonical_doi"] for item in groups.values()
        if item["canonical_doi"] is not None
    })
    if unseen:
        raise ValueError(f"verified metadata has DOI absent from source matrix: {unseen}")
    keyed = [groups[key] for key in sorted(groups)]
    return {
        "schema_version": "1.0.0",
        "catalog_scope": "source_derived_doi_keys_not_a_verified_systematic_review",
        "source_draft_sha256": {key: value["sha256"] for key, value
                                 in source["sources"].items()},
        "verified_metadata_sha256": review_sha,
        "source_mention_count": len(source["rows"]),
        "distinct_candidate_work_keys": len(keyed),
        "reviewed_metadata_work_count": sum(
            item["metadata_status"] == "reviewed_metadata" for item in keyed),
        "unverified_doi_work_count": sum(
            item["metadata_status"] == "draft_doi_unverified" for item in keyed),
        "unresolved_no_doi_work_count": sum(
            item["metadata_status"] == "unresolved_no_doi" for item in keyed),
        "curated_doi_typo_mentions": sum(
            row["resolution"] == "curated_doi_typo_alias"
            for item in keyed for row in item["mentions"]),
        "legacy_label_doi_mismatch_count": source["citation_status_counts"].get(
            "numbered_reference_doi_mismatch", 0),
        "records": keyed,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DRAFTS)
    parser.add_argument("--catalog", action="store_true",
                        help="export DOI-keyed work candidates and reviewed metadata")
    parser.add_argument("--verified-metadata", type=Path, default=VERIFIED)
    parser.add_argument("--output", type=Path,
                        help="write machine-readable JSON (exclusive creation)")
    args = parser.parse_args()
    try:
        report = (catalog(args.source_dir, args.verified_metadata)
                  if args.catalog else audit(args.source_dir))
        serialized = json.dumps(report, indent=2, sort_keys=True,
                                ensure_ascii=False, allow_nan=False) + "\n"
        if args.output is None:
            print(serialized, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
