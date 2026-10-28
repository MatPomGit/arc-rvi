"""Regression tests for unverified secondary bibliography coverage."""
import csv
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pytest

from scripts.audit_full_literature_archive import (
    FINAL_EXPORTS, audit, normalize_doi, normalize_title,
)


def body(rows):
    handle = io.StringIO()
    fields = ("Paper Title", "DOI", "Publication Year", "Paper Link", "Relevant Excerpt")
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def test_secondary_doi_is_only_an_unscreened_candidate():
    with TemporaryDirectory() as folder:
        archive = Path(folder) / "sample.zip"
        with ZipFile(archive, "w") as dest:
            for name in FINAL_EXPORTS:
                dest.writestr(name, body([{
                    "Paper Title": "Shared <sup>2</sup>",
                    "DOI": "https://doi.org/10.1111/shared",
                    "Publication Year": "2024", "Paper Link": "",
                }]))
            dest.writestr("scispace_fulltext_extra.csv", body([
                {
                    "Paper Title": "Shared 2", "DOI": "10.1111/shared",
                    "Publication Year": "2024", "Paper Link": "",
                    "Relevant Excerpt": "excerpt",
                },
                {
                    "Paper Title": "New paper", "DOI": "DOI:10.9999/new",
                    "Publication Year": "2025", "Paper Link": "",
                    "Relevant Excerpt": "unverified extracted text",
                },
            ]))
        summary, queue = audit(archive)
    assert summary["final_row_mentions"] == 8
    assert summary["secondary_row_mentions"] == 2
    assert summary["secondary_doi_strings_not_in_final"] == 1
    assert summary["secondary_normalized_titles_not_in_final"] == 1
    assert summary["fulltext_named_csv_excerpt_rows"] == 2
    assert len(queue) == 1
    assert queue[0]["doi"] == "10.9999/new"


def test_normalization_and_required_exports():
    assert normalize_doi("https://doi.org/10.1234/ABC") == "10.1234/abc"
    assert normalize_title("Robot <sup>2</sup>") == "robot2"
    with TemporaryDirectory() as folder:
        archive = Path(folder) / "incomplete.zip"
        with ZipFile(archive, "w") as dest:
            dest.writestr("misc.csv", body([]))
        with pytest.raises(ValueError, match="missing final exports"):
            audit(archive)
