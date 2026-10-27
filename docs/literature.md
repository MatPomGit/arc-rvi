# Literature evidence and publication gates

**Status:** editorial triage of four author-supplied research drafts, 2026-10-27.
**Not** a completed systematic review, DOI audit, preregistration, or publication clearance.
Canonical publication decisions remain governed by the [research programme](../experiments/README.md),
[methodology](methodology.md) and [project state](project-state.md).

The full submitted drafts are preserved without editorial rewriting in the
[research/literature/source_drafts repository directory](https://github.com/MatPomGit/arc-rvi/tree/main/research/literature/source_drafts).
They are **unverified supporting material**, not sources of validated empirical results.

## Intake and traceability

| Submitted file | Purpose | Source SHA-256 |
| --- | --- | --- |
| `ARC_RVI_Literature_Review.md` | Narrative review of P01–P08 | `0ca2d5a14d55dc11585c0459adb6233a9e749c8fab0e4bf5e9caf1ec573191f6` |
| `ARC_RVI_Literature_Evidence_Matrices.md` | Study-specific evidence tables | `9451979f3fdf3b13bc42e0ad24d475294daecb664ebc78203142ad51734b6594` |
| `ARC_RVI_Gap_Analysis_Publication_Strategy.md` | Gap ranking and draft publication strategy | `60c6e8562f490a5153dd5a51c25fef2898df45a57648a9e66fd53806e533b6b4` |
| `ARC_RVI_Hypotheses_Experimental_Recommendations.md` | Candidate hypotheses, conditions, endpoints and datasets | `4aa21ff4f8de6d591336f152cee9780e44fe373e2a6541fb9ea0e18e65cb79d1` |

Hashes identify the submitted local file versions; their original formatting and wording
were not peer-reviewed by ARC-RVI. Full drafts are kept **outside the MkDocs staging tree**
to avoid presenting unverified numerical statements as verified research.

The main narrative claims approximately **1,908 unique screened publications**,
while the gap analysis reports **240 analyzed articles (30 per direction)**.
The attached evidence matrix contains **79 tabulated entries** across eight research
directions (9 for P01 and 10 each for P02–P08). The four appendices each include
a separate 30-entry reference list. These quantities describe the **supplied files**,
not an independently reconstructed screening flow. A complete deduplicated export,
dated search strings, inclusion/exclusion decisions, paper-to-claim linkage,
and reproducible count reconciliation are **missing**.

Citation labels such as `[1]` are **local to the individual sections and drafts**:
they are not unique bibliographic identifiers across the four files.
The numbered appendix bibliography includes DOI
[10.7717/peerj.7086](https://doi.org/10.7717/peerj.7086), which is an
eye-tracker test battery, **not autonomous robotic inspection evidence**.
Its specific relevance must be justified or its use removed.
Two spot-checked entries do match their described research areas:
[VPR-Bench](https://doi.org/10.1007/s11263-021-01469-5)
and [robotic cylindrical-cavity inspection](https://arxiv.org/abs/2608.16442).
These checks do **not** validate the remaining bibliographic metadata,
quantitative gap counts, study summaries or novelty assertions.

## Research directions and evidence thresholds

| Study | Candidate contribution from supplied review | Provisional primary outcome (see canonical protocol) | Publication blocker / competing scope |
| --- | --- | --- | --- |
| [P01](../experiments/exp01_benchmark/protocol.md) | Reproducible inspection-specific robustness benchmarking | Paired change in performance between nominal and perturbed conditions | Validate scene realism, inspection endpoint, independent families; do not claim a new SOTA algorithm |
| [P02](../experiments/exp02_localization/protocol.md) | Identity-safe localization among visually similar instances | Wrong-instance selection per eligible request | Natural-image validation and ground-truth pose/identity calibration; do not duplicate P03 planning |
| [P03](../experiments/exp03_viewpoint_planning/protocol.md) | Feasibility-aware coupled viewpoint and motion planning for G1 EDU | Valid required coverage under a shared motion budget | Verified URDF, constraints, collision/stability model and matched baseline |
| [P04](../experiments/exp04_active_coverage/protocol.md) | Active coverage with incomplete geometry | Budget-capped time to target coverage | Observation-only updates; isolate online uncertainty from P03 known-geometry planning and P06 recovery |
| [P05](../experiments/exp05_repeatability/protocol.md) | Reproducible camera acquisition geometry | Across-session capture-pose precision | Independent calibrated physical pose reference; images are not independent sessions |
| [P06](../experiments/exp06_quality_control/protocol.md) | Quality-feedback recovery with bounded reacquisition | Reference-valid coverage gained by recovery | External quality oracle and common deadline; distinguish P04's incomplete-geometry search |
| [P07](../experiments/exp07_transfer/protocol.md) | Validated visibility/coverage prediction bias | Independent physical coverage prediction error | Calibrated physical outcomes, prediction lock before evaluation; simulation alone insufficient |
| [P08](../experiments/exp08_field_validation/protocol.md) | Integrated autonomous-vs-manual documentation | Blinded paired required-region coverage / proposed noninferiority | Human approval, physical acquisition, prespecified margin, independent scoring and order effects |

This matrix identifies **candidate research boundaries**. It is not a finding of
novelty or an assurance that eight separately publishable papers exist.
The gap draft's “high publication readiness” labels for P01/P03/P06 must be
treated as **aspirational potential**, because the necessary validations and
datasets do not yet exist. Consolidate overlapping manuscripts when a unique
primary contribution cannot be demonstrated.

## Prioritized, falsifiable design proposals

1. **P01, benchmark sensitivity.** Use the supplied lighting suggestions
   (100, 500, 1,000, 2,000 lux), placement variations (±10 cm, ±15°),
   and occlusion proportions (0, 25, 50, 75%) as an **unfrozen candidate
   factorial grid**, not calibrated levels. Declare the primary paired
   contrast, independent object-family unit, geometry/reference scale and
   severity calibration before sampling.
2. **P03, feasible planning.** Compare a fixed-base/manipulator-adapted
   baseline with a genuinely whole-body-aware method under the *same*
   inspection task and budget. Define kinematic/stability/collision
   feasibility externally to either planner and audit camera frame transforms.
   Do not equate a planar model or static URDF audit with bipedal stability.
3. **P06, proactive versus reactive quality.** Pair disturbances and budgets.
   Count poor acquisitions, accepted valid coverage, retries, rejected
   observations, missed observations and deadline failures. An independent
   image-quality evaluator must not reuse the policy's acceptance threshold.
4. **P07, model-fidelity prediction.** Before seeing held-out physical results,
   lock nominal/geometrically calibrated/full-model predictions on identical
   tasks. Analyze signed bias and absolute coverage prediction error
   by independent object/session, including calibration uncertainty.

The supplied experiment suggestions (e.g. `n ≥ 30` per condition,
expected F or t statistics, “80% power for medium effects”) are **not
validated sample-size calculations**. A 4×3×4 design with 30 recordings
per cell totals 1,440 observations but does not imply 1,440 independent units.
Repeated observations nested in object and session require hierarchical,
clustered, or blocked inference. The absence of statistical significance
alone neither falsifies an effect nor proves equivalence.
Do not freeze any trial number, alpha allocation, effect margin, hypothesis
or threshold from these drafts without a pilot variance model, sensitivity
analysis, explicit multiplicity plan, and independent confirmation split.

## DOI, novelty and evidence release gate

Before inserting citations into `papers/references.bib` or promoting a claim:

1. Verify the DOI resolves to the **same title, authors, venue and year**;
   record a stable publisher/preprint URL and date of verification.
2. Link every quoted finding to a **specific source and experiment**.
   Flag secondary summaries, arXiv-only status, unmeasured claims,
   dataset mismatch and non-representative platform comparisons.
3. Rebuild an exportable inclusion/exclusion inventory for each P01–P08
   search, deduplicate DOI/preprint/version variants, and reconcile 1,908,
   240 and 79. Do not state verified prevalence fractions until complete.
4. Create one research-claim register for each paper: baseline and
   independent primary endpoint, upstream dependencies, shared
   objects/sessions, current evidence level, calibration and ethical gates.
5. Require source revisions, declared independent units, holdout sealing,
   predeclared thresholds and uncertainties before a *confirmatory* report.
   Report simulations as simulations; no physical claims without measured data.

**Current decision:** P01–P08 are **not ready for submission**.
The supplied drafts are useful for literature discovery and protocol design;
they do not themselves establish discovery of a research gap, reproducible
systematic review, experiment completion or manuscript readiness.
