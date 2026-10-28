# Study 06: Closed-Loop Quality-Aware Image Acquisition for Autonomous Robotic Inspection

Protocol version: 1.1.2

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does quality-guided reacquisition increase valid surface coverage at a fixed mission
time compared with quality-triggered retries that do not change viewpoint?
This isolates recovery policy from the repeatability mechanism studied in study 05.

Proposed hypothesis: Quality-guided replanning increases valid coverage relative to same-view retries at the same time budget.

## Design and baselines
Inject controlled focus, exposure and occlusion perturbations in held-out scenes.
For physical trials, use measured perturbations within the approved operating envelope.
Compare one-shot acquisition, fixed exposure brackets, same-view quality retries and
quality-guided viewpoint replanning. Give all methods equal total mission time.
Ablate focus, exposure and visibility feedback separately.

Calibrate quality thresholds on development images using an independent reference
criterion. The evaluator must not simply reuse the policy's own acceptance flag.
Freeze processing scale and units for focus and exposure features; thresholds depend
on that processing definition.

## Endpoint and failure
The primary endpoint is area-weighted coverage whose images pass the frozen independent
quality criterion by the deadline. Count a surface element once even after many retries.
Report rejected-image rate, false acceptance, retry count, time and unresolved regions.

Freeze retry limits, per-action timeouts and stopping policy before confirmation.
Retry exhaustion, no reachable replacement view and deadline expiry are recorded failures.
A missing or corrupted image contributes no valid coverage. Retain previous valid
coverage after an abort and report the abort reason separately.
Record every attempt, including failed attempts, to expose resource consumption.

## Unit, analysis and acceptance
The independent unit is an object/session scene, with paired perturbation schedules.
Estimate paired valid-coverage differences with object/session clustering appropriate
to the sampling design. Do not treat retries or frames as independent trials.
Before confirmation, verify perturbation strength, evaluator calibration, action timing
and retry accounting. The existing threshold helper is not an implemented feedback loop.

## Humanoid gait-induced acquisition failures (unfrozen)

A humanoid's balance correction, foot impacts, torso pitch/roll,
camera-head vibration and terrain occlusion can degrade exposure,
motion blur and ROI coverage *while walking or after stopping*.
Separate camera/sensor loss from instability-driven capture
failure. Compare acquisition during safe approved motion,
immediately after a stop, a fixed settling-delay policy and
a motion-state-conditioned quality trigger **only when physical
safety and independent motion references allow it**.

Keep the same difficult-terrain route and validated contact
limits across methods. A good static image is not sufficient if
obtaining it required an unsafe stance, unapproved movement,
omitted failure or exceeded deadline. Count all such trials as
failures for the predeclared inspection-success endpoint; report
image-quality conditional on successful safe acquisition only as
a secondary outcome. No new numerical thresholds are adopted
from locomotion literature.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 06](../../papers/paper06/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Literature-derived proactive/reactive distinction

The [literature intake](../../docs/literature.md) proposes proactive
quality-aware viewpoint selection versus post-hoc filtering and reacquisition.
Use this as a **secondary ablation** of the existing primary replanning-versus-
same-view-retry question, with a shared deadline, matched disturbances and a
reference evaluator independent from the policy score. This trial must not
reuse P04's online incomplete-geometry endpoint as independent evidence.
Suggested image-quality cutoffs and trial counts are not calibrated.

## Full-method comparator appraisal (2026-10-28)

The [publisher full-text Zhao et al. (2026)](https://www.mdpi.com/2076-3417/16/18/9389)
shows a constrained, **quality-gated active re-observation** comparator,
not just a passive quality filter: one 4-DoF Dobot eye-in-hand stereo
system, six scenes, 60 sample cases and four feasible candidate views
per case. It reports initial/online/manual-offline ROI evaluability of
70.0% / 76.7% / 93.3%, respectively. Its **paired mean-Q** online-minus-
initial 95% bootstrap CI is **[−0.008, 0.060]**; this interval includes
zero and does **not** establish a definitive mean quality gain. The
paper explicitly lacks independently measured reference depths.

**Additional unfrozen comparator:** implement or faithfully approximate
a bounded feasible-view, ROI-quality-gated **top-1 re-observation policy**
and compare it with same-view retry, exposure/gain optimisation and
P06's proposed quality-guided replanning. Record any unimplemented
sensor-model elements and mark an approximation as such. Freeze a
**separate external quality/inspection-coverage reference** before
confirmatory tests; reusing the policy's ROI stereo score as the
evaluator would introduce circularity.

**Statistical guard:** scene/session identity, not the 60 correlated
case-level images of a single six-scene study, controls independent
inference. Report paired effects and intervals clustered by scene/
object family; count failed/no-image/retry-exhausted cases and all
their time costs at the common mission deadline. No threshold or
sample count from the external paper is imported as a calibrated
ARC-RVI parameter.

Source grading and the 2026 Staderini thesis overlap are documented
in the [evidence matrix](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/evidence_to_experiments_2026-10-28.md).

## Publication overlap guard (2026-10-27)

[Zhao et al. (2026)](https://doi.org/10.3390/app16189389) already present
quality-aware active re-observation for constrained eye-in-hand manipulators.
[Bégin & Hunter (2022)](https://doi.org/10.3390/s22030835) study active exposure
control for visual localization and [Kim et al. (2020)](https://doi.org/10.1109/TRO.2020.2985597)
study proactive camera control for visual navigation. Therefore this proposal
cannot treat quality-aware re-observation or proactive exposure as novel on
their own. The **unconfirmed** study contribution is independent quality-
scored inspection coverage at a common action/time budget, with clear failure
and re-observation denominators. Bibliographic matching alone does not verify
these papers' experimental performance claims; consult the full methods before
freezing baselines.

## Distinct prior-art domains

[Deng et al. (2024)](https://doi.org/10.1016/j.rcim.2023.102619)
study predictive image exposure in robotic **disassembly**;
[Zhang et al. (2022)](https://doi.org/10.3390/s22249641)
study synchronized stereo-DIC **metrology** exposure, not robot inspection;
and [Shin et al. (2019)](https://doi.org/10.1109/IROS40897.2019.8968590)
study noise-aware exposure for robot vision. These are useful controls
for exposure and image-quality estimation, but cannot be presented as
equivalent to independent inspection-valid surface coverage or autonomous
recovery. Add their comparable scores only where units and data are compatible.

## Secondary comparator registration: closed-loop sensing recovery (2026-10-28, unfrozen)

The [source-row-grounded review ledger](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/secondary_comparator_decisions.json)
makes [FRA-NBV](https://doi.org/10.1109/LRA.2026.3728374)
an explicit **reflectivity and missing-depth reacquisition** comparator and
[RASP](https://doi.org/10.1109/TASE.2025.3604455)
a **joint view-planning/depth-completion** contextual method comparator.
Both are prior art for quality-aware active sensing. They cannot be cited
as evidence that any ARC-RVI physical inspection quality improvement exists.
Primary full-method and outcome extraction remain pending.

The matched-budget pilot matrix shall cross image degradation mechanisms
(specular missing depth, blur, exposure, occlusion, pose/motion disturbance)
with (a) no-retry; (b) fixed same-view retry; (c) bounded photometric
exposure control; (d) feasible-view quality-gated reobservation, including
an incidence-aware surrogate when reflective sensing is relevant.
A source-faithful RASP baseline may be added **only** after its depth
completion component, training inputs and datasets are independently
inspected and reproducible; otherwise record it as contextual prior art.

Freeze one shared **mission time**, image budget and view-feasibility/safety
oracle across comparable arms. The independent evaluator must score
inspection-valid regions **without using the policy's own quality score**
and must count each assigned scene's no-image, exhausted-retry,
unsafe-reposition and intervention outcomes. Predefine separate
conditional strata for reflective material and challenging bipedal
motion; no broad physical transfer inference from current planar fixtures.

## Reflective car paint as the principal quality failure (prospective, 2026-10-28)

The [vehicle mission contract](../../docs/vehicle-inspection-missions.md)
makes **specular saturation/highlights on the actual requested part**
a first-class failure condition. A bumper photograph with high focus
but a saturated defect-relevant ROI is **not** automatically acceptable.
Define independently annotated part masks, saturation/glare fraction
inside each mask, exposure/focus/motion blur, pose-dependent reflections
and a blinded assessor's inspection-valid verdict. Fix cutoffs from
development/calibration data, not by fitting confirmation images.

Compare within identical mission budgets: no retry; same-view retry;
exposure/gain/HDR control; safely changed camera incidence angle;
and an optional calibrated polarizing/controlled-lighting arm *only
if the verified sensor provides it*. Record action count, clock time,
safety-limited moves, no-image, clipping, failed re-acquisition and
whether the requested region becomes independently accepted. A
glare-free background with an unusable shiny bumper remains a failure.

[Staderini et al. 3DV 2024](https://doi.org/10.1109/3DV62453.2024.00108)
already consider specular BRDF-aware photometric viewpoint optimisation;
[van Ruitenbeek & Bhulai 2022](https://doi.org/10.1007/s00138-022-01295-w)
study multi-view vehicle damage inspection under reflections, and
[He et al. 2024](https://doi.org/10.1016/j.jmsy.2023.11.014)
address specular car-body defect images. These limit broad novelty
claims; the proposed distinct endpoint is *robotically executed,
independent inspection-valid car/part acquisition at a matched budget*.
No measured optical benefit is asserted.
