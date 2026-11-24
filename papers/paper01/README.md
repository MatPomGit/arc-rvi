# Paper 01

Working title: **Reproducible Simulation Benchmark for Autonomous Robotic Visual Inspection**

Experimental source: `experiments/exp01_benchmark/protocol.md`.

This directory contains a manuscript **template**, not publishable findings.
Prepare only evidence-backed claims; cite prior work and clearly distinguish
shared datasets from new hypotheses and analyses. Keep generated figures here
only when cleared for public release.

## Publication plan (author decision, 2026-11-24)

Portfolio identifier: MSC-RVI-P01 (local study P01).
Primary venue: [ICAISC 2027](https://icaisc.eu/), conditional GO.
Status: planned, simulation only, not submitted or accepted.
Preserve the original working title and protocol until a justified amendment.
Candidate conference title: *Robust Viewpoint Planning for Robotic Visual Inspection under Environmental Uncertainty: A Simulation-Based Benchmark*.

The conference study will compare fixed-order, coverage-greedy and distance-greedy
planning under the declared synthetic geometry, occlusion, illumination and clutter
conditions. An adaptive fuzzy planner is a proposed extension, subject to novelty
review, feasibility and a protocol amendment before confirmation. It must not
receive evaluator-only information or a different mission budget. Retain the
primary paired success-degradation contrast and account for all failed attempts.
Use family-disjoint partitions, justified sample counts, uncertainty intervals,
ablations and reproducible code/configuration/seed receipts. Unsupported sensor
or illumination effects must be explicitly excluded from robustness claims.
No physical robot trials, participant recruitment or new expenditure are in scope.

### Target schedule

| Date (2026) | Deliverable |
| --- | --- |
| 24-27 Nov | Literature and novelty audit, pilot design, protocol lock criteria |
| 28 Nov-03 Dec | Implement and verify baselines and candidate fuzzy planner; freeze design before confirmation |
| 04-09 Dec | Run eligible simulation experiments, paired analysis and ablations |
| 10-15 Dec | Draft Springer conference manuscript, tables, figures and limitations |
| 16-18 Dec | Evidence audit, anonymous PDF and author GO/NO-GO package |
| 19-22 Dec | Final corrections and author-authorized submission only |

Target readiness: 18 December 2026. Planned submission deadline: 22 December
2026; verify current official requirements, deadline, fees and indexing before
submission. Follow existing issues [#21](https://github.com/MatPomGit/arc-rvi/issues/21),
[#22](https://github.com/MatPomGit/arc-rvi/issues/22),
[#38](https://github.com/MatPomGit/arc-rvi/issues/38) and
[#39](https://github.com/MatPomGit/arc-rvi/issues/39).
If evidence or novelty is inadequate, record NO-GO rather than submit unsupported claims.

### Potential subsequent publications

- Applied Soft Computing: substantially new adaptive planning methods and experiments.
- Robotics and Autonomous Systems: substantially extended simulation and separately authorized physical validation.

These journals are provisional options, not commitments. Verify fit, fees and
publication requirements. Any extension must have a distinct scientific contribution,
transparent citation of the conference work and no duplicate submission or primary
finding presented as independent confirmation.
