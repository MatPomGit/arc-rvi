# ARC-RVI: exhaustive coverage of the supplied literature ZIP (2026-10-28)

**Status: offline export inventory, NOT an independently validated systematic review.**
Related to [the selected eight-export audit](export_audit_2026-10-28.md),
[the canonical research-integrity gate](../../docs/literature.md) and
[the DOI/work-identity issue #70](https://github.com/MatPomGit/arc-rvi/issues/70).

## Why this addition is needed

The contributor's `agent-artifacts-rvi.zip` is byte-identical to the archive
already audited as `agent-artifacts-zip_robo.zip`: full ZIP SHA-256
`603a6d1369466b160c29234bb4db8dd6d2247999f62835d0964ad95fb9a6e69f`.
Consequently this is **not a new literature collection** and the eight
selected final datasets and four drafts must **not be re-imported**.

The earlier 1,907-row inventory accurately counts the **eight selected final
exports**, but does not count the additional *candidate identifiers* that
appear in the other 147 CSV exports. Calling all of those exports redundant
would miss a substantial unscreened candidate pool.

## Whole-archive counts

| Audit dimension | Offline count | Interpretation |
| --- | ---: | --- |
| All CSV exports | 155 | Eight selected final; 147 other/intermediate |
| Final export row mentions | 1,907 | Existing canonical inventory; **not unique publications** |
| Secondary export row mentions | 9,582 | May repeat final rows and each other |
| Total CSV row mentions | 11,489 | **Not a screening denominator** |
| Distinct syntactically valid DOI strings in final exports | 1,300 | Same as existing audit |
| Distinct syntactically valid DOI strings in secondary exports | 4,158 | Includes final-export DOI strings |
| DOI strings found in secondary but **not** final exports | **2,858** | Unscreened *identifier queue*, NOT additional verified papers |
| Normalized titles in final / secondary | 1,682 / 4,528 | Strict text normalization, not work identity |
| Normalized titles in secondary but not final | **2,846** | Unscreened title forms, NOT additional independent studies |
| Files named `scispace_fulltext_*.csv` | 28 | Naming is not evidence of a paper read |
| Row mentions in these named full-text exports | 2,800 | Every row has a nonempty `Relevant Excerpt` field |

CSV member hashes and source-row locations are reconstructed by the
[offline audit script](../../scripts/audit_full_literature_archive.py);
no full-text downloads or external bibliographic resolution occur here.
Distinct DOI *strings* can include preprint/publisher relations, version
duplicates, irrelevant works or inaccurate metadata. Title normalization
removes punctuation, accents and HTML tags, but cannot establish study identity.

## Interpretation and evidence boundary

1. Preserve the canonical eight-export inventory, its DOI/work reconciliation,
   the 79-entry draft-matrix inventory and 22 previously checked DOI metadata
   records **without overwriting them**.
2. Do not append 9,582 secondary mentions to the 1,907 selected mentions as
   independent studies. Do not reinterpret 2,858 additional DOI strings as
   2,858 eligible RVI papers or as evidence that any proposed gap exists.
3. The `Relevant Excerpt` fields are **unverified exported excerpts**:
   some contain bibliographic or keyword text rather than an auditable passage
   supporting a method, quantitative outcome, physical robot or claim.
   They are leads for retrieving primary source documents, not reviewed full
   texts.
4. Screen secondary-only identifiers in a **separate queue** with provenance,
   relevance/exclusion reasons, source version and human review; check
   version relations against the existing 1,695 provisional candidates.
5. Prioritize candidate direct comparators for **P03/P04/P06** (viewpoint,
   coverage, imaging quality), **P07** (geometry/sensor sim-to-real), and
   **P08** (independent inspection acceptance). For the difficult-terrain
   Unitree G1 EDU programme, separate *humanoid locomotion context* from
   measured **humanoid inspection** outcomes.
6. Any candidate that survives topical screening still needs externally checked
   DOI/title/author/year, primary full-text methods and comparator assessment.
   No publication go/no-go state changes on the strength of these counts.

## Reproduction

With the source ZIP present locally, run:

```bash
python scripts/audit_full_literature_archive.py /path/to/agent-artifacts-rvi.zip \
  --output-dir /tmp/rvi-full-archive-audit
python scripts/validate.py
```

Outputs: `archive_coverage.json` (including per-export SHA-256 and row
denominators) and `secondary_only_doi_queue.csv` (2,858 DOI strings with
example title, first filename, data-row position and mentions).
This queue is reproducible, generated *locally* and intentionally **not
committed as confirmed publication metadata**.

**Scientific disposition:** no new empirical research findings, no verification
that all exported excerpts accurately represent full text, no completed PRISMA
flow, and no relaxation of the publication evidence gates.
