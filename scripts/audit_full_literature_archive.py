"""Audit the complete ARC-RVI archive without treating search hits as verified studies."""
from __future__ import annotations

import argparse
import csv
import hashlib
from html import unescape
import io
import json
from pathlib import Path
import re
import unicodedata
from zipfile import ZipFile

FINAL_EXPORTS = (
    "final_combined_robotic_inspection_benchmarking.csv",
    "combined_object_instance_localization_final.csv",
    "combined_viewpoint_motion_planning_complete.csv",
    "combined_active_coverage_nbv_results.csv",
    "combined_robot_camera_repeatability_results.csv",
    "final_comprehensive_image_quality_results.csv",
    "combined_sim_to_real_results.csv",
    "final_combined_autonomous_inspection_2018_2026.csv",
)
REQUIRED = {"Paper Title", "DOI", "Publication Year", "Paper Link"}
DOI = re.compile(r"^10\.\d{4,9}/\S+$")
MAX_FILE_SIZE = 8_000_000


def normalize_doi(value: str) -> str:
    return re.sub(
        r"^(?:doi\s*:\s*|https?://(?:dx\.)?doi\.org/)",
        "", value.strip(), flags=re.I,
    ).strip().lower().rstrip("/")


def normalize_title(value: str) -> str:
    text = re.sub(r"<[^>]*>", "", unescape(value))
    text = unicodedata.normalize("NFKD", text.replace("ł", "l").replace("Ł", "L"))
    return re.sub(
        r"[^a-z0-9]+", "", text.encode("ascii", "ignore").decode().lower()
    )


def audit(archive: Path) -> tuple[dict, list[dict]]:
    if not archive.is_file():
        raise FileNotFoundError(archive)
    with archive.open("rb") as source_file:
        archive_sha = hashlib.file_digest(source_file, "sha256").hexdigest()
    groups = {
        "final": {"dois": set(), "titles": set(), "rows": 0},
        "secondary": {"dois": set(), "titles": set(), "rows": 0},
    }
    files: list[dict] = []
    secondary_by_doi: dict[str, dict] = {}
    with ZipFile(archive) as source:
        entries = [
            f for f in source.infolist()
            if f.filename.lower().endswith(".csv") and not f.is_dir()
        ]
        names = [x.filename for x in entries]
        if len(names) != len(set(names)):
            raise ValueError("duplicate CSV member names")
        missing = sorted(set(FINAL_EXPORTS) - set(names))
        if missing:
            raise ValueError(f"missing final exports: {missing}")
        for item in sorted(entries, key=lambda x: x.filename):
            if item.file_size > MAX_FILE_SIZE:
                raise ValueError(f"CSV member too large: {item.filename}")
            raw = source.read(item)
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError(f"missing required columns in {item.filename}")
            group = "final" if item.filename in FINAL_EXPORTS else "secondary"
            count = excerpt_rows = missing_doi = invalid_doi = 0
            for rownum, row in enumerate(reader, start=1):
                if None in row:
                    raise ValueError(f"malformed CSV at {item.filename}#{rownum}")
                count += 1
                doi = normalize_doi((row.get("DOI") or "").strip())
                title = (row.get("Paper Title") or "").strip()
                tkey = normalize_title(title)
                if not doi:
                    missing_doi += 1
                elif DOI.fullmatch(doi):
                    groups[group]["dois"].add(doi)
                    if group == "secondary":
                        secondary_by_doi.setdefault(doi, {
                            "doi": doi, "title_example": title,
                            "first_source": item.filename,
                            "first_row": rownum, "mentions": 0,
                        })["mentions"] += 1
                else:
                    invalid_doi += 1
                if tkey:
                    groups[group]["titles"].add(tkey)
                if "Relevant Excerpt" in row and (
                    row["Relevant Excerpt"] or ""
                ).strip():
                    excerpt_rows += 1
            groups[group]["rows"] += count
            files.append({
                "source_file": item.filename,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "group": group,
                "row_mentions": count,
                "missing_doi": missing_doi,
                "invalid_doi": invalid_doi,
                "nonempty_excerpt_rows": excerpt_rows,
            })
    a, b = groups["final"], groups["secondary"]
    queue = [secondary_by_doi[d] for d in sorted(b["dois"] - a["dois"])]
    summary = {
        "status": "offline_unverified_export_inventory",
        "source_sha256": archive_sha,
        "csv_files": len(files),
        "final_csv_files": sum(f["group"] == "final" for f in files),
        "secondary_csv_files": sum(f["group"] == "secondary" for f in files),
        "final_row_mentions": a["rows"],
        "secondary_row_mentions": b["rows"],
        "all_row_mentions": a["rows"] + b["rows"],
        "final_distinct_doi_strings": len(a["dois"]),
        "secondary_distinct_doi_strings": len(b["dois"]),
        "secondary_doi_strings_not_in_final": len(b["dois"] - a["dois"]),
        "final_distinct_normalized_titles": len(a["titles"]),
        "secondary_distinct_normalized_titles": len(b["titles"]),
        "secondary_normalized_titles_not_in_final": len(b["titles"] - a["titles"]),
        "fulltext_named_csv_files": sum(
            "fulltext" in f["source_file"].lower() for f in files
        ),
        "fulltext_named_csv_row_mentions": sum(
            f["row_mentions"] for f in files
            if "fulltext" in f["source_file"].lower()
        ),
        "fulltext_named_csv_excerpt_rows": sum(
            f["nonempty_excerpt_rows"] for f in files
            if "fulltext" in f["source_file"].lower()
        ),
        "file_inventory": files,
        "interpretation": (
            "Secondary-only strings are unscreened candidate identifiers; "
            "neither unique studies nor independently verified full texts."
        ),
    }
    return summary, queue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary, queue = audit(args.archive)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "archive_coverage.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with (args.output_dir / "secondary_only_doi_queue.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("doi", "title_example", "first_source", "first_row", "mentions"),
        )
        writer.writeheader()
        writer.writerows(queue)
    print(json.dumps(
        {k: v for k, v in summary.items() if k != "file_inventory"},
        indent=2, ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
