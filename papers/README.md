# Manuscript workspace

Eight independent paper workspaces correspond one-to-one to experiment
protocols. Manuscripts are drafts; no result should be written as an achieved
claim without measurements and analysis.

Manuscript author metadata may identify the repository owner. Third-party
bibliography entries must truthfully record original authors and works.
Co-author credits must always reflect actual contributions. Check data rights,
funding acknowledgment obligations, ethical approvals, and relevant licenses
before submission or public release.

Generated figures belong in each paper's `figures/` after clearance.
`references.bib` contains shared citation records only when verified.

The [literature intake audit](../docs/literature.md) documents submitted draft
reviews, unresolved bibliographic provenance and cross-paper novelty risks.
Do not transfer draft references to `references.bib` or characterize a manuscript
as submission-ready until each claim has an independently verified source and
its prospective experimental gate has been satisfied.

Stable DOI-derived **candidate identifiers** are available via
`python scripts/audit_literature.py --catalog` and the ten reviewed bibliographic
records are documented in [the literature audit](../docs/literature.md).
An ID is not peer review or replication. The full article must be examined
for the actual claimed experimental evidence and rechecked for rights before
using its citation in a manuscript.
