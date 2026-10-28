# Study 07: Closing the Sim-to-Real Gap in Autonomous Humanoid Visual Inspection

Protocol version: 1.1.1

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does calibrated bounded randomization improve prediction of physical valid coverage
compared with nominal simulation? Keep the inspection policy fixed in this study.
Study 07 concerns predictive transfer, not a second evaluation of policy improvement.

Proposed hypothesis: Calibrated bounded randomization reduces physical-coverage prediction error relative to nominal simulation.

## Design and baselines
Separate physical sessions into calibration, model selection and held-out confirmation.
Keep object instances and sessions disjoint between calibration and confirmation.
Estimate camera, pose and actuation error distributions only on calibration sessions.
Compare nominal simulation, predeclared wide randomization, calibrated deterministic
parameters and calibrated bounded randomization. Give each the same simulation budget.
Ablate sensor, localization and actuation error models separately.

Create matched scenario descriptions from information available before the physical
outcome is observed. Generate simulated predictions before opening held-out results.
Freeze the number of simulator replicates per physical scenario; report Monte Carlo
uncertainty separately from variation among physical sessions.

## Endpoint and failure
The primary endpoint is absolute error between predicted mean valid coverage and
observed physical valid coverage, computed per held-out matched scenario.
Report signed error, prediction-interval coverage and interval width as secondary
endpoints. Also report physical success, localization and timing discrepancies.
Good predictive agreement does not itself demonstrate acceptable physical performance.

Physical aborts remain outcomes under the common coverage rule. Missing reference
measurements are marked unavailable and counted; they are not replaced by simulator
output. Explain any unmatched scenarios and report a sensitivity analysis.

## Unit, analysis and acceptance
The independent unit is a physical object/session scenario. Simulated replicates
estimate its prediction and do not increase the physical sample size.
Compare paired absolute errors with intervals clustered by physical session and object
as required by the design. Freeze parameter identifiability checks, bounds, budget
and held-out partition before confirmation. Requires a validated simulator, authorized
robot access and reference measurements; fixtures cannot test transfer.

## Terrain/contact sim-to-real validity gate (unfrozen)

The flat, holonomic planar model cannot predict terrain
interaction of a humanoid: foot sole contact and friction,
slip, slope, stair ascent/descent, whole-body swept collision,
torso/head motion and camera optical blur during gait.
Before any terrain-transfer claim, independently validate
the exact robot URDF and contact/dynamic model, foot
geometry, camera-to-body transforms and sensor timestamps
on a **separate authorized calibration dataset**.

Declare a supported terrain envelope and reject
out-of-envelope, unknown-traction or unsupported contact
states as **unverified**; never turn model failure into
zero-error prediction. Primary error remains based on
held-out *physical inspection-valid coverage*.
Report separately locomotion failure, pose error,
contact-estimation discrepancy, real-camera rejection,
missing reference and site intervention, with sessions
as units. No physical data exist yet and neither
an external G1 paper nor planar smoke tests validate G1 EDU transfer.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 07](../../papers/paper07/manuscript.tex).
Publication boundaries: [research program](../README.md).

## Literature-derived fidelity and bias audit

The [literature intake](../../docs/literature.md) motivates explicit
self-occlusion, external-occlusion and sensor-limit strata, and nominal,
geometrically calibrated and sensor-calibrated prediction controls.
Compare signed coverage bias, absolute prediction error and missing
physical reference measurements on frozen held-out object/session units.
This is an extension of the existing predictive-transfer endpoint, not
a claim that “full calibration” works or that measured physical sessions
have already been collected.

## Vehicle-paint and lighting domain shift (prospective, 2026-10-28)

The [vehicle-mission protocol](../../docs/vehicle-inspection-missions.md)
requires an explicit transfer question: does synthetic predicted
glare/visibility at planned car/bumper poses correspond to independently
measured photographs of reflective automotive paint under varying
sunlight, overcast conditions, garage lighting, wetness, trim/glass
materials and paint colours? Freeze material and illumination families,
lens/exposure/polarization state and actual robot camera configuration.

Report independent ROI saturation/defect-visibility prediction error
and calibration on held-out physical vehicles, **separately** from
P03 feasibility, P04 coverage and P06 bounded recovery treatment
effects. A BRDF simulator and synthetic data cannot establish a
physical transfer result or a valid G1 EDU terrain/actuator model.
Hardware calibration, ground-truth region annotation and sensor
synchronisation are mandatory physical gates.
