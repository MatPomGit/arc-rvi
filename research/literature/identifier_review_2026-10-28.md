# Identifier collisions and initial relevance triage (2026-10-28)

**Status:** source-extraction QA and *limited manual* metadata/relevance checks, not a complete eligibility screening or full-text evidence appraisal. Issues: [#70](https://github.com/MatPomGit/arc-rvi/issues/70), [#71](https://github.com/MatPomGit/arc-rvi/issues/71), [#72](https://github.com/MatPomGit/arc-rvi/issues/72). Input is the eight pinned CSVs identified in [export audit](export_audit_2026-10-28.md). Source archive is not published.

## Reproducible collision counts and provenance

After ignoring HTML markup in source titles (e.g. `<sup>*</sup>`) and normalizing accents, the script detects **one DOI grouping with differing normalized title strings** (not the earlier two), and **six identical normalized titles associated with multiple DOI strings**. The source locator `filename#N` means the *N-th CSV data record* (1-based, excluding header), not a physical CSV text line. For original, full titles and exact source rows run the script and inspect `identifier_conflicts.json`.

| Collision type | DOI or DOI pair | Source record(s) | Assessment |
| --- | --- | --- | --- |
| One DOI; differing titles | `10.1117/12.2502203` | P01 `final_combined_robotic_inspection_benchmarking.csv#155`; P08 `final_combined_autonomous_inspection_2018_2026.csv#142` | P08 title is visibly truncated. **Not evidence of a different publication**; independent canonical-title review pending |
| Potential manuscript versions | `10.1109/iros47612.2022.9982063` / `10.48550/arxiv.2208.04391` | P02/P03/P06 | Matching normalized title, relation pending |
| Potential manuscript versions | `10.1109/iros47612.2022.9981472` / `10.48550/arxiv.2207.10543` | P02/P04 | Matching normalized title, relation pending |
| Potential manuscript versions | `10.1109/tfr.2026.3733788` / `10.48550/arxiv.2603.04284` | P03/P04 | *OmniPlanner*: matching title/author list in [arXiv](https://arxiv.org/abs/2603.04284) and [journal metadata index](https://eurekamag.com/research/110/972/110972090.php); **probable versions of one work**, publisher/version relationship still to be checked |
| Potential manuscript versions | `10.1016/j.oceaneng.2019.106420` / `10.5281/zenodo.4253168` | P06/P08 | Matching normalized title, repository/publisher relation pending |
| Potential manuscript versions | `10.1145/3570731` / `10.48550/arxiv.2307.15363` | P01/P08 | Matching normalized title, relation pending |
| Potential manuscript versions | `10.3390/robotics12040108` / `10.48550/arxiv.2306.06969` | P03/P06 | Matching normalized title, relation pending |

The `10.1109/ISAS59543.2023.10164352` source titles differ only because one CSV retains `<sup>*</sup>` markup. This is a **formatting artifact**, removed by HTML-stripping normalization, not a work-identity collision. [Institutional conference metadata](https://scholarsmine.mst.edu/civarc_enveng_facwork/2624/) identifies the paper as Li et al., *Hardware-in-the-loop and Digital Twin Enabled Autonomous Robotics-assisted Environment Inspection* (ISAS 2023). This is bibliographic identification, not verification of its performance claims.

## First manual relevance assessment

| Work | Source row | External evidence | Review decision |
| --- | --- | --- | --- |
| [Ehinger et al. (2019), `10.7717/peerj.7086`](https://pubmed.ncbi.nlm.nih.gov/31328028/) | P01 `final_combined_robotic_inspection_benchmarking.csv#1`, P08 `final_combined_autonomous_inspection_2018_2026.csv#50` | PubMed and [full-text HTML](https://pmc.ncbi.nlm.nih.gov/articles/PMC6625505/) confirm an **eye-tracker data-quality comparison**, not autonomous robot inspection | **Exclude from direct robotic-inspection performance or novelty evidence**; may retain as cross-domain quality/measurement methodology with justification. The supplied relevance score of 75/100 is not authoritative |
| [Li et al. (2023), `10.1109/ISAS59543.2023.10164352`](https://scholarsmine.mst.edu/civarc_enveng_facwork/2624/) | P01 `#87`, P08 `#236` (full filenames above) | Institutional bibliographic record and abstract describe digital-twin/HIL environmental inspection with aerial robotics and preliminary evaluation | **Relevant methodological comparator** for digital-twin testing, not evidence of G1 EDU humanoid physical validation. Full methods and numerical claims unverified |

The above are **two manually assessed DOI identities**, not a count of distinct screened studies or completed systematic review. Review date: 2026-10-28. No automated exclusion is applied to the remaining 1693 candidate keys.

## Verified work-version links (2026-10-28)

Four of the six potential multi-DOI work identities have supporting primary bibliographic evidence; two remain pending. Their exact DOI decisions, sources and limitations are recorded in [work-version review](work_version_review_2026-10-28.md) and the [curated version manifest](work_version_relations.json). The separate work-level grouping may produce **1691 provisional keys**, not independently screened or eligible articles. Source citations and original DOI strings are retained.

## Next gates

- Resolve all six potential work-version relations against original publisher/preprint version metadata and record accepted work-level merges *separately* from immutable export-row identities.
- Independently resolve the truncated SteamVR record before using its citation; link exact DOI/title and original P08 row without inventing missing text.
- Review the unassessed **435** provisional candidate keys with explicit inclusion/exclusion criteria; no bulk machine-generated eligibility or false full-text review claims.
- Only after work-level reconciliation estimate unique eligible studies and rebuild a dated search/screening flow. The source claims 1908→240→79 remain unsupported as a single flow.
