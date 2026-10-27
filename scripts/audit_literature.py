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
DOI = re.compile(r"\b10\.\d{4,9}/[^\s|,;)\]>]+", re.IGNORECASE)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DRAFTS)
    parser.add_argument("--output", type=Path,
                        help="write machine-readable JSON (exclusive creation)")
    args = parser.parse_args()
    try:
        report = audit(args.source_dir)
        serialized = json.dumps(report, indent=2, sort_keys=True,
                                ensure_ascii=False, allow_nan=False) + "\n"
        if args.output is None:
            print(serialized, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
