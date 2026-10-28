# ARC-RVI literature-export audit (2026-10-28)

**Scope:** a reproducible, offline **bibliographic inventory**, not a systematic review or evidence of a treatment/robot-performance effect. This audit uses the eight selected *final/complete* CSV exports from the contributor-supplied archive (SHA-256: `603a6d1369466b160c29234bb4db8dd6d2247999f62835d0964ad95fb9a6e69f`). The source archive is intentionally not published in this repository. Its four MD drafts differ from the previously preserved four source drafts. Do not overwrite the archival copies.

## Selected source files

| Study | Selected CSV export | Records | Missing DOI |
| --- | --- | ---: | ---: |
| P01 | final_combined_robotic_inspection_benchmarking.csv | 222 | 27 |
| P02 | combined_object_instance_localization_final.csv | 281 | 104 |
| P03 | combined_viewpoint_motion_planning_complete.csv | 302 | 62 |
| P04 | combined_active_coverage_nbv_results.csv | 150 | 38 |
| P05 | combined_robot_camera_repeatability_results.csv | 114 | 29 |
| P06 | final_comprehensive_image_quality_results.csv | 368 | 63 |
| P07 | combined_sim_to_real_results.csv | 221 | 66 |
| P08 | final_combined_autonomous_inspection_2018_2026.csv | 249 | 25 |
| **Total** | **Eight specified CSVs** | **1907** | **414** |

The other 147 CSV exports in the same archive may be intermediate searches or overlapping lists; adding their rows to this final inventory would double-count the collection.

## Reconstructed, algorithmic counts

- **1907** exported row mentions; **1695** provisional candidate keys under a deterministic DOI-first, normalized-title-fallback grouping; **212** duplicate row mentions by that rule.
- **1300** different syntactically plausible DOI strings. DOI format checks **do not resolve the DOI or verify the article**.
- Missing/invalid fields among 1907 row mentions: **414** DOI; **207** year; **274** abstract; **130** author field; **2** title.
- **2** DOI keys map to differing normalized titles; **6** normalized titles map to more than one DOI. Preprint/publisher versions and erroneous metadata must be resolved manually. Do not automatically merge those six title cases.
- **436** candidate keys carry at least one of the generator's screening flags (missing DOI, year, title disagreement or potential preprint/publisher version). This is a **triage queue**, not a confirmed number of erroneous articles.

The **1695 is not a count of unique publications**: (i) different DOIs can refer to versions of one study; (ii) the same title can refer to different studies; (iii) DOI-free entries can overlap DOI-bearing entries; (iv) eligibility and publication status were not verified. The older narrative's **1908** and **240** are source claims and cannot be taken as reconciled PRISMA stages. The separate matrix audit covers **79** detailed table mentions (77 candidate work keys) and previously recorded **64** local bracket-reference DOI mismatches. These datasets and counting rules are distinct.

## Provenance of selected CSVs (SHA-256)

| Study | File hash |
| --- | --- |
| P01 | b4549543f9384577e8253acdd49876836c46c45835f81f4ae025554c207e6425 |
| P02 | 9189290c2ae605aecceebd4d9175460fe7733cf4d7d7b8668138b002780b2a48 |
| P03 | 82ace3473ceb3bda604ae05decf367cc94923ced28aba5deeaf29a0c184715ee |
| P04 | 225ce29cec2678fa44435200ceb9a4a1fdfbd114cdfc84081c26323e1a5a0ad9 |
| P05 | a36b7687c6d4139ed4954b70ee15517b03a77453613c14fe4aa60acb4774b2a1 |
| P06 | 38ffa219757d21a0546b6e016a96afea20f2458b8fbe328ec51ed8c7a210cacd |
| P07 | 1cea215508373e7db616f86b8dec4518ebf355ceb143ea11e65ffd200ab5ed09 |
| P08 | afee2bd88759714baaa10566aae2d4eb11bf0601185d5be8466e045311013712 |

## Reproduction and evidence limits

With the user-provided ZIP available locally, run:

    python scripts/audit_literature_exports.py /path/to/agent-artifacts-zip_robo.zip --output-dir /tmp/rvi-literature-20261028

Outputs are a machine-readable summary JSON, a candidate CSV with source-record locations, and a flagged screening queue. The script does not connect to publishers, assert that abstracts were actually read, or upgrade the 79-row curated metadata catalogue. Keep paper-to-claim links and research results outside this inventory until separately assessed.

Follow the [critical synthesis](critical_synthesis_2026-10-28.md), [experiment-specific evidence map](evidence_to_experiments_2026-10-28.md), existing [DOI metadata manifest](verified_doi_metadata.json), and [canonical editorial gate](../../docs/literature.md).
