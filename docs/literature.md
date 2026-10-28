# Literature evidence and publication gates

## Eight-export bibliographic inventory, 2026-10-28

A newly supplied ZIP contains 155 CSV exports. Eight explicitly selected complete/final datasets contain **1907 row mentions** and produce **1695 provisional DOI-first/title-fallback keys**; these are **not confirmed unique eligible studies**. There are **414 missing DOI fields**, **207 missing/invalid years**, **274 missing abstracts**, **130 missing author fields**, and **2 empty titles**. The screening queue flags **435 candidate keys**. One remaining DOI has divergent normalized title strings, and six titles have multiple DOI identifiers; four work-version pairs have been bibliographically linked and two remain unresolved (see [review](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/work_version_review_2026-10-28.md)); this changes the derived provisional work grouping to 1691 keys, without confirming eligibility. Title normalization now strips HTML superscripts (one earlier collision was an artifact). A dated [source-row identity/relevance review](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/identifier_review_2026-10-28.md) documents two initial external checks, without treating them as full-text appraisal. This collection is **distinct** from the earlier 79-row curated evidence-matrix inventory, and it does not establish the drafts' 1908→240 screening flow.

- [Reproducible source-hash and count audit](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/export_audit_2026-10-28.md)
- [New critical eight-study synthesis](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/critical_synthesis_2026-10-28.md)
- [Evidence-to-experiment and publication gates](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/evidence_to_experiments_2026-10-28.md)
- Offline command: python scripts/audit_literature_exports.py /path/to/agent-artifacts-zip_robo.zip --output-dir /tmp/arc-rvi-export-audit

The offline `python -m scripts.reconcile_literature_versions` step accepts **only four explicitly reviewed pairs**, preserves two uncertain relations unmerged, and emits a source-pinned reconciliation receipt. See the [version-link manifest](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/work_version_relations.json).

**Manual relevance review, 2026-10-28:** five candidates have
individually sourced decisions (one direct prior art, two contextual, two
excluded from direct-inspection claims); **1690 remain unreviewed**.
This is not the **435**-candidate data-quality queue, and neither
count is a PRISMA screening stage. The
[manual decision manifest](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/manual_screening_decisions.json)
and `python -m scripts.screen_reviewed_literature` reproduce a
source-pinned, non-destructive screening receipt. The
[OmniPlanner full-text appraisal](prior-art-critical.md) documents
existing cross-morphology inspection planning and field deployments,
without verifying an IEEE publisher DOI or a humanoid experiment.

**New direct-comparator extraction, 2026-10-28:** the
[P03/P04/P06 evidence matrix](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/evidence_to_experiments_2026-10-28.md)
now distinguishes (1) abstract-only prior art in Staderini IROS 2024,
Bettles arXiv 2026, and the Staderini 2026 doctoral thesis from
(2) a source-method/result appraisal of Zhao et al. (2026) based on
publisher HTML. The thesis includes **photometric visibility plus
kinematic feasibility and route optimisation**; thus broad joint
quality-aware planning is not a defensible novel contribution.
Zhao's reported online-minus-initial paired quality interval crosses
zero, and independently measured depth references are absent. All
source-level effect summaries remain external reports, **not**
ARC-RVI results. The P03/P04/P06 protocols now name stronger
conceptual comparators and independent test oracles.

**Humanoid/difficult-terrain scope, 2026-10-28:** the robot in
ARC-RVI is a **bipedal Unitree G1 EDU reference platform** intended
for **challenging terrain and constrained inspection access**,
not an ordinary level-floor mobile base. The
[primary-source G1 prior-art appraisal](prior-art-critical.md)
differentiates *published* rough-terrain locomotion, indoor humanoid
inspection and **not-yet-tested terrain-conditioned inspection**;
physical Unitree G1 claims must not be transferred to the actual G1
EDU hardware without device/sensor/controller verification. The
[prospective terrain registry](population.md),
[simulator validity boundary](simulation.md) and
[physical safety gate](safety.md) explicitly mark all contact/terrain
factors unsupported in current planar software. The
[study-specific evidence matrix](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/evidence_to_experiments_2026-10-28.md)
defines disjoint P03–P08 endpoints and failure denominators, with
no new ARC-RVI experiment or physical deployment reported.

**Editorial control:** original drafts and the 22-item reviewed DOI manifest remain unchanged; no imported CSV record is automatically labeled bibliographically verified.

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

## Reproducible bibliographic inventory (partial reconstruction)

The offline inventory checks the **numbering and DOI fields in these four
source files**, not publisher metadata or systematic search completeness.
Run from the repository root:

```bash
python scripts/audit_literature.py --output results/arc_rvi_literature_inventory.json
```

The report is content-addressed with the SHA-256 of all four source drafts;
the command exclusively creates an output file and refuses to overwrite it.
The JSON lists the study, matrix source line, cited label, table DOI, numbered
bibliography DOI and a mismatch category for **every row**.

| Checked quantity | Value | Interpretation |
| --- | ---: | --- |
| Study-specific matrix rows | 79 | P01: 9; P02–P08: 10 each |
| Rows with a parseable DOI | 73 | String present, **not externally verified** |
| Rows without DOI | 6 | Work identification requires manual bibliographic follow-up |
| Unique DOI strings in matrix | 71 | Two DOI strings each occur in two study matrices |
| Entries in appended references | 30 | **The same 30-entry block** appears in all four drafts |
| Matrix label resolves to same DOI as appended bibliography | 9 | String match only |
| Matrix label resolves to a **different** DOI | **64** | Unusable numbered citation until repaired |
| Matrix row without a DOI | 6 | Label linkage unresolved without source verification |

Examples: P03 `Human-Inspired Inspection [1]` has DOI
`10.3390/biomimetics11050296`, while the shared bibliography's
`[1]` points to `10.7717/peerj.7086`, an eye-tracker assessment.
P02 `ActivePose [8]` likewise has an arXiv DOI different from the
shared bibliography item `[8]`. These are **numbering collisions**,
not evidence that either corresponding publication is nonexistent.

The two multiply counted matrix DOI strings are
`10.48550/arxiv.2603.16471` (P03/P04) and
`10.1088/1361-6501/adf3d4` (P05/P08).
Repeated study *mentions* must not become independent papers or
independent support for a research gap. The **79** matrix rows, the
draft's **240** selected works and the reported **1,908** unique
retrievals are separate unverified counting stages, not an
established PRISMA-style flow. The available exports cannot confirm
the inclusion criteria, exact overlap or deduplication.

### Dated external bibliographic spot checks

| DOI | Status on 2026-10-27 | Implication for ARC-RVI |
| --- | --- | --- |
| [10.1007/s11263-021-01469-5](https://link.springer.com/article/10.1007/s11263-021-01469-5) | VPR-Bench, Zaffar et al., *IJCV* (2021): title, year and VPR benchmarking subject checked against publisher | Supports standardized viewpoint/appearance variation methodology, **not** direct proof of robotic inspection superiority |
| [10.3390/s26154757](https://www.mdpi.com/1424-8220/26/15/4757) | ROEP, Han & Choi, *Sensors* 26(15), 4757 (2026): DOI, title and authors checked against publisher | Deployment-facing VLA evaluation; not a humanoid inspection trial |
| [10.1016/j.cacaie.2026.100007](https://doi.org/10.1016/j.cacaie.2026.100007) | *Toward next-generation autonomous structural health monitoring and inspection with humanoid robots*, Wang et al. (2026), publisher page checked | **Material prior art**: RoboInspect reports two physical humanoid inspection case studies; P03/P08 novelty must be narrower than “first humanoid inspection” |
| [10.7717/peerj.7086](https://pubmed.ncbi.nlm.nih.gov/31328028/) | Ehinger et al. (2019), *PeerJ*: DOI/title checked against PubMed | A test battery for Pupil Labs/EyeLink eye-tracking, not an autonomous robotic inspection benchmark |

The earlier external spot checks covered only those **four individual DOI records**,
not the full matrix, all abstracts or any reported quantitative gap rate.
Do not label the entire bibliography verified based on this table.

## DOI-keyed work catalogue and metadata gate (v1.22)

The machine-readable catalogue **replaces ambiguous bracket numbers in the
working index**, but **does not silently rewrite the four original drafts**.
An identifier is constructed from a DOI in a matrix cell, not from the
incompatible appended bibliography. DOI-less entries get visibly provisional
`unresolved:pXX:...` keys. Multiple study mentions of the same normalized
DOI are grouped under one candidate work. DOI string equality and a
matching key do **not** demonstrate the existence or relevance of an article.

```bash
python scripts/audit_literature.py --catalog \
  --output results/literature_work_catalog.json
```

The catalogue includes each source matrix row and line, its original bracket
number, original and corrected DOI when applicable, source collision status,
and one of three verification levels:

- `reviewed_metadata`: DOI/title/year and first-author information where
  available inspected at the explicitly recorded publisher, university
  repository or scholarly index page; **not** article-level evidence verification
- `draft_doi_unverified`: the DOI appears only in the submitted draft; it has
  **not** been checked against publisher metadata
- `unresolved_no_doi`: no reliable source identifier supplied; **do not
  invent a DOI or import the item into BibTeX**

One reviewed alias corrects the P03 matrix's trailing `/pdf`
(`10.1051/matecconf/202541305002/pdf`) to the actual DOI
`10.1051/matecconf/202541305002`, supported by the university
repository. Original matrix text remains untouched.

**Current source-derived catalogue:** 79 mentions map to **77 distinct
candidate keys**: **22 checked-metadata DOI works**, **49 unchecked DOI
works** and **6 unresolved DOI-free records**. Two DOI records occur
twice across studies. The pre-existing **64 legacy number↔DOI conflicts**
remain documented as defects of the input drafts; the new stable keys bypass
them in downstream indexing rather than pretending that the draft has been
repaired.

The 22-record curated metadata manifest is
[`research/literature/verified_doi_metadata.json`](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/verified_doi_metadata.json).
Its DOI, title, venue/year, editorial relevance, verification date and
source URLs are reviewed inputs. The catalogue rejects malformed metadata,
ambiguous correction aliases and reviewed DOIs missing from the matrix.
Both the raw drafts and curated manifest are SHA-256 pinned in the report.

### Initial ten matrix DOI records checked against external bibliographic pages

| Study | DOI | Bibliographic record / primary relevance |
| --- | --- | --- |
| P01 | [10.1007/s11263-021-01469-5](https://link.springer.com/article/10.1007/s11263-021-01469-5) | Zaffar et al., 2021, *VPR-Bench*; visual place recognition, **not** inspection-specific physical coverage |
| P01 | [10.3390/s26154757](https://www.mdpi.com/1424-8220/26/15/4757) | Han & Choi, 2026, ROEP; VLA manipulation evaluation |
| P08 | [10.1016/j.cacaie.2026.100007](https://www.sciencedirect.com/science/article/pii/S1093968726018153) | 2026 RoboInspect; **existing physical humanoid inspection case studies** |
| P03 | [10.1051/matecconf/202541305002](https://bura.brunel.ac.uk/handle/2438/32281) | Zhang et al., 2025; offline-IK mobile arm planning, corrected malformed DOI |
| P06 | [10.3390/app16189389](https://www.mdpi.com/2076-3417/16/18/9389) | Zhao et al., 2026; quality-aware active re-observation prior art |
| P08 | [10.3390/app12042250](https://www.mdpi.com/2076-3417/12/4/2250) | Aust & Pons, 2022; human vs machine blade inspection, **not humanoid** |
| P08 | [10.1061/(asce)co.1943-7862.0002322](https://ascelibrary.com/doi/10.1061/%28ASCE%29CO.1943-7862.0002322) | Xia et al., 2022; human–robot **simulated** emergency structural inspection |
| P06 | [10.3390/s22030835](https://www.mdpi.com/1424-8220/22/3/835) | Bégin & Hunter, 2022; auto-exposure for mobile robot localization |
| P06 | [10.1109/tro.2020.2985597](https://snu.elsevierpure.com/en/publications/proactive-camera-attribute-control-using-bayesian-optimization-fo/) | Kim et al., 2020; proactive camera attribute control for navigation |
| P04 | [10.1109/icra.2018.8461098](https://dblp.org/rec/conf/icra/BorderG018.html) | Border et al., 2018, Surface Edge Explorer, checked via bibliographic index |

**Limit:** these initial ten records verify *bibliographic identification* against
a named external page, not experimental validity, data independence,
replication, novelty, a full abstract-by-abstract review or search
completeness. A separate older checked eye-tracker DOI
(`10.7717/peerj.7086`) appears in the appended reference list but
**not** the 79-row evidence matrix; it is not part of the 22-item
working catalogue.

### Methodological consequences

- P06 cannot claim that *quality-aware re-observation* or proactive
  camera attribute control is itself new. The possible research question
  is whether an **independently scored, budget-matched closed-loop
  recovery policy** improves inspection-valid coverage on a humanoid.
- P08 cannot claim the first human–machine comparison or first
  humanoid inspection demonstration. Its prospective contribution is an
  **assessor-blinded, common-task manual vs autonomous acquisition
  comparison** with explicit physical validity and uncertainty.
- P03's coupling of whole-body feasibility and acquisition quality is
  a candidate comparison, but prior offline-IK mobile-manipulator work
  constrains simplistic claims of novelty.

Before writing any verified scientific claim, inspect the source's
methods and measurements separately, not just the DOI metadata.
The claimed 1,908→240 screening flow remains **unreconstructed**.

For detailed comparison of new directly competing publications, see the
[critical prior-art appraisal](prior-art-critical.md). This separates
bibliographic metadata from reported experimental evidence and changes
P02/P03/P04/P06/P08 novelty boundaries.

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
