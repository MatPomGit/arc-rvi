# Study 05: Influence of Humanoid Locomotion and Camera Pose on Visual Acquisition Repeatability

Protocol version: 1.1.0

Status: prospective design, not preregistered or frozen

## Question and primary contrast
Does motion-state-conditioned capture reduce repeat-acquisition position error
relative to a fixed settling-delay reference?
This study estimates acquisition repeatability rather than mission completeness.

Proposed hypothesis: Motion-state-conditioned capture reduces within-block position dispersion relative to fixed-delay capture.

## Design and baselines
Use randomized blocks crossing object, camera pose, approach direction and motion state.
Compare capture during permitted movement, immediate capture after stopping, a fixed
settling delay and a motion-state-conditioned trigger.
Hold optics, exposure, scene and target pose constant within each block.
Randomize method order; log temperature, time since startup and approach history.

Separate trigger development from confirmation sessions. Obtain camera pose from an
independent reference system, not the same estimator used by the trigger.
Synchronize reference and image timestamps and quantify reference uncertainty.
A physical procedure must specify permitted motion, interlocks and stop authority.

## Endpoint and failure
The primary endpoint is the root mean square distance, in metres, of repeated camera
positions from their within-block centroid. This measures precision, not absolute accuracy.
Define a fixed number of approaches per block before collection.
Report orientation repeatability in degrees, signed pose bias against the requested
pose, focus variation and settling time as secondary endpoints.

A missing capture has no position error value. Record it as a capture failure and
report completion separately. Exclude incomplete blocks only under the predeclared
missingness rule; include a sensitivity analysis for method-related dropout.
Do not describe a method as more repeatable solely because unstable trials disappeared.

## Unit, analysis and acceptance
The independent replication unit is a separately initialized acquisition session.
Approaches and images are nested within session/object blocks.
Compare block-level repeatability between paired methods using session-clustered intervals;
a mixed-effects sensitivity model may include object and session effects.
Freeze reference resolution, trigger thresholds, settling delay, repeats and session
count after a separate pilot. Simulation can test noise models but cannot replace
physical repeatability measurements.

## Provenance and confirmation gate

Apply the [shared analysis plan](../analysis/README.md) and
[run-record contract](../../docs/reproducibility.md). Retain failures and deviations.
Before confirmation, record numeric thresholds, sample-size justification, dataset
partitions, exact baseline revisions and the analysis implementation in an immutable
protocol release. No confirmation data may be used to tune these choices.

Manuscript: [paper 05](../../papers/paper05/manuscript.tex).
Publication boundaries: [research program](../README.md).
