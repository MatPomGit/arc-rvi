# Incoming literature research drafts — unverified

These four files are user-supplied research inputs preserved for provenance.
**Not peer-reviewed, independently verified, or publication-ready.**
Statements about publication counts, significance, novelty, robot performance,
target venues and suggested experiments are **claims or recommendations in the
source drafts**, not measured results from ARC-RVI.

Use the editorial [literature audit and evidence gates](../../docs/literature.md)
and [study protocols](../../experiments/README.md) before citing or adapting.
The drafts are stored outside the MkDocs staging tree. Bibliographic labels
are local to each draft. Review and verify each DOI before transferring entries
to `papers/references.bib`. Do not overwrite these reference copies during
editing; create curated changes in the canonical documentation instead.

Original user-upload SHA-256:
- `ARC_RVI_Literature_Review.md`: `0ca2d5a14d55dc11585c0459adb6233a9e749c8fab0e4bf5e9caf1ec573191f6`
- `ARC_RVI_Literature_Evidence_Matrices.md`: `9451979f3fdf3b13bc42e0ad24d475294daecb664ebc78203142ad51734b6594`
- `ARC_RVI_Gap_Analysis_Publication_Strategy.md`: `60c6e8562f490a5153dd5a51c25fef2898df45a57648a9e66fd53806e533b6b4`
- `ARC_RVI_Hypotheses_Experimental_Recommendations.md`: `4aa21ff4f8de6d591336f152cee9780e44fe373e2a6541fb9ea0e18e65cb79d1`

## Offline bibliography inventory

Run `python scripts/audit_literature.py --output results/literature_inventory.json`
to export the machine-readable DOI/numbering audit. This script never
contacts Crossref, arXiv or publisher servers and **does not verify** authors,
publication dates, experimental claims or the 1,908/240 search denominators.
All four archival drafts remain byte-for-byte unchanged.

## DOI-keyed research catalogue

Run `python scripts/audit_literature.py --catalog --output results/literature_work_catalog.json`.
The 22 checked-metadata DOI records reside in `verified_doi_metadata.json` with
review date and source URLs. Catalogued unverified DOI strings and provisional
DOI-free items **must not** be copied into `papers/references.bib` or cited
as verified primary evidence. Duplicate DOI mentions are grouped across studies.

The [critical prior-art appraisal](../../docs/prior-art-critical.md) distinguishes
reported physical manipulator/field trials, simulated Gazebo evidence,
metrology-only methods and arXiv publication status. None of these
records by itself validates the eight ARC-RVI research contributions.

## Additional exported bibliographic search corpus (2026-10-28)

The contributor's later archive has a different SHA-256 and different MD-draft hashes from the four archival source files above. It has **not** replaced those files. See the [pinned eight-export audit](export_audit_2026-10-28.md), [critical synthesis](critical_synthesis_2026-10-28.md), and [prospective evidence-to-experiment map](evidence_to_experiments_2026-10-28.md). The reproducible import command is documented in the audit; the private/local ZIP itself is not committed. Neither 1907 export rows nor 1695 candidate keys should be cited as a systematic screening denominator. The [identifier and relevance triage](identifier_review_2026-10-28.md) records seven flagged identity groups, a corrected 435-key initial screening queue and two manually assessed example works; these are not a completed review.
