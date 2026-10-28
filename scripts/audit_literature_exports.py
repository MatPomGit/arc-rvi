"""Audit eight ARC-RVI CSV literature exports offline, without dependencies."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
from zipfile import ZipFile

STUDIES = {
    "P01": "final_combined_robotic_inspection_benchmarking.csv",
    "P02": "combined_object_instance_localization_final.csv",
    "P03": "combined_viewpoint_motion_planning_complete.csv",
    "P04": "combined_active_coverage_nbv_results.csv",
    "P05": "combined_robot_camera_repeatability_results.csv",
    "P06": "final_comprehensive_image_quality_results.csv",
    "P07": "combined_sim_to_real_results.csv",
    "P08": "final_combined_autonomous_inspection_2018_2026.csv",
}
REQUIRED = {"Paper Title", "DOI", "Publication Year", "Author Names", "Abstract", "Paper Link"}
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")


def normalized_doi(value: str) -> str:
    result = re.sub(r"^(?:doi\s*:\s*|https?://(?:dx\.)?doi\.org/)", "", value.strip(), flags=re.I)
    return result.strip().lower().rstrip("/")


def normalized_title(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value.replace("ł", "l").replace("Ł", "L")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", plain)


def audit(archive: Path) -> tuple[dict, list[dict], list[dict]]:
    issues = Counter()
    hashes = {}
    counts = {}
    groups = defaultdict(list)
    doi_titles = defaultdict(set)
    title_dois = defaultdict(set)
    with ZipFile(archive) as source:
        for study, filename in STUDIES.items():
            raw = source.read(filename)
            hashes[filename] = hashlib.sha256(raw).hexdigest()
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if not REQUIRED.issubset(reader.fieldnames or ()):
                raise ValueError(f"missing columns in {filename}")
            counts[study] = 0
            for record_number, row in enumerate(reader, start=1):
                counts[study] += 1
                original_doi = (row["DOI"] or "").strip()
                doi = normalized_doi(original_doi)
                title = (row["Paper Title"] or "").strip()
                title_key = normalized_title(title)
                year = (row["Publication Year"] or "").strip()
                for field, missing in (("DOI", "missing_doi"),
                                       ("Abstract", "missing_abstract"),
                                       ("Author Names", "missing_authors")):
                    if not (row[field] or "").strip():
                        issues[missing] += 1
                if not re.fullmatch(r"(?:19|20)\d{2}", year):
                    issues["missing_or_invalid_year"] += 1
                if not title_key:
                    issues["missing_title"] += 1
                valid_doi = bool(DOI_PATTERN.fullmatch(doi))
                if doi and not valid_doi:
                    issues["invalid_doi_format"] += 1
                key = "doi:" + doi if valid_doi else (
                    "title:" + title_key if title_key else f"row:{study}:{record_number}")
                record = {
                    "study": study, "source_file": filename,
                    "source_record": record_number, "title": title,
                    "doi": doi, "year": year,
                    "paper_link": (row["Paper Link"] or "").strip(),
                }
                groups[key].append(record)
                if valid_doi:
                    doi_titles[doi].add(title_key)
                    if title_key:
                        title_dois[title_key].add(doi)
    candidates = []
    screening = []
    for key in sorted(groups):
        records = groups[key]
        first = records[0]
        candidate_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        status = "provisional_doi" if key.startswith("doi:") else "provisional_title"
        if key.startswith("row:"):
            status = "missing_title_and_doi"
        flags = []
        if len({normalized_title(r["title"]) for r in records}) > 1:
            flags.append("title_disagreement")
        if any(not r["year"] for r in records):
            flags.append("year_missing")
        if status != "provisional_doi":
            flags.append("doi_missing_or_invalid")
        if any(len(title_dois.get(normalized_title(r["title"]), set())) > 1 for r in records):
            flags.append("possible_preprint_journal_pair")
        item = {
            "candidate_id": candidate_id, "status": status,
            "title": first["title"], "doi": first["doi"], "year": first["year"],
            "studies": ";".join(sorted({r["study"] for r in records})),
            "source_records": ";".join(
                f'{r["source_file"]}#{r["source_record"]}' for r in records),
            "mentions": len(records), "flags": ";".join(sorted(set(flags))),
            "paper_link": first["paper_link"],
        }
        candidates.append(item)
        if flags:
            screening.append(item)
    report = {
        "scope": "Eight selected CSV exports; no DOI resolution, full-text checking or eligibility screening",
        "source_archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "source_files_sha256": hashes,
        "study_record_counts": counts,
        "export_records": sum(counts.values()),
        "candidate_keys": len(candidates),
        "duplicate_mentions_by_key": sum(counts.values()) - len(candidates),
        "unique_valid_doi_strings": len(doi_titles),
        "doi_with_conflicting_titles": sum(len(titles) > 1 for titles in doi_titles.values()),
        "titles_with_multiple_dois": sum(len(dois) > 1 for dois in title_dois.values()),
        "missing_fields": dict(sorted(issues.items())),
        "screening_queue_candidates": len(screening),
        "limitation": "Candidate keys are not verified unique publications; preprint/journal pairs and false matches require review",
    }
    return report, candidates, screening


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report, candidates, screening = audit(args.archive)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names = ["summary.json", "work_candidates.csv", "screening_queue.csv"]
    if any((args.output_dir / name).exists() for name in names):
        parser.error("output exists; choose a new output directory")
    (args.output_dir / names[0]).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    columns = list(candidates[0])
    for name, records in [(names[1], candidates), (names[2], screening)]:
        with (args.output_dir / name).open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(records)
    print(json.dumps({
        "export_records": report["export_records"],
        "candidate_keys": report["candidate_keys"],
        "screening_queue_candidates": len(screening),
    }))


if __name__ == "__main__":
    main()
