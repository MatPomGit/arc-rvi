# Study 06: Closed-Loop Quality-Aware Image Acquisition for Autonomous Robotic Inspection

Protocol version: 1.1.0

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
