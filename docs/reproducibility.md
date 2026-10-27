# Reproducibility contract

Version: 1.3.0

## Run and trial records

The following fields specify the proposed research record. The [fixture benchmark](benchmark.md)
and [planar simulator](simulation.md) implement documented subsets. The
[exploratory experiment batch interface](experiment-batches.md) now adds grouped
Study 01 simulation/fixture trial records, deterministic outputs, hashes and
UTC receipts. It does **not** yet implement the entire cross-study contract,
physical recording, crash-timeout recovery or secure sealed confirmation. Keep private measurements and large assets outside Git.
Use anonymous technical identifiers in public manifests.

| Record | Required fields and meaning |
| --- | --- |
| Run identity | `schema_version`, `run_id`, `study_id`, `protocol_version`, UTC start/end |
| Evidence | `evidence_type`: `fixture`, `simulation` or `physical` |
| Source | Full commit SHA, dirty-tree flag, dependency/environment record hash |
| Configuration | Immutable input configuration path and SHA-256, method revision |
| Data | Dataset revision, rights record, split manifest hash, calibration revision |
| Randomness | Scene, noise, method and analysis seeds; PRNG implementation |
| Trial identity | Unique `trial_id`, `run_id`, paired `scenario_id`, method ID, replicate ID |
| Grouping | Object, geometry family, session and operator codes as applicable |
| Conditions | Factor values, units, start state, budget, trial order and period |
| Outcome | Status, failure reason, primary endpoint, secondary measurements |
| Artifacts | Relative paths, byte sizes, hashes and reference-measurement links |

A source revision alone is insufficient for a modified working tree. Archive the diff
and its hash, or rerun from a clean revision for confirmation.
Do not normalize timestamps, units or missing values silently during analysis.
Missing measurements use explicit null values and reason codes, never NaN or fabricated zeros.

## Outcome vocabulary

Use `completed`, `algorithm_failure`, `timeout`, `safety_abort`,
`measurement_missing` or `infrastructure_failure` as terminal trial status.
Record more specific reasons separately. Status does not define endpoint scoring;
apply the study protocol to partial coverage, capped time or absent pose measurements.
Link replacements to the original trial and retain both records.

Use one trial record per initiated method/scenario/replicate combination.
Every method in a paired comparison must reference the same scenario specification.
Store actual sampled perturbations or their reproducible generator revision and inputs.
Store configuration hashes with the original bytes, not a reserialized substitute.

## Evidence compatibility

The existing `rvi plan` command writes `evidence_type: synthetic_fixture`.
Treat this legacy label as `fixture` only at an explicit future import boundary and
preserve the original label in provenance. Do not relabel fixture output as simulation.
The current image-manifest helper records file hashes; it does not capture all fields above.

## Freeze and rerun

Before confirmation, archive the protocol, baselines, evaluator, partition specification,
thresholds and sample-size calculation under immutable revisions with hashes.
A protocol draft in Git is not proof of public preregistration.
Record any registration service and identifier only after registration actually occurs.

The user-supplied programming instruction v1.8 (sections 8, 11, 14 and
the ROS 2/TF2 exercise) identifies specific **future capture checks**:
joint/IMU state and action timestamps, RGB/depth acquisition completeness,
LiDAR `frame_id`, TF2 tree connectivity, and logs of commands, actual
states, failures and operator intervention. Record clock source, time offset,
sensor frame conventions and dropped-message counts. Its example RGB/depth
timestamp tolerance is a *teaching target*, not a calibrated or frozen
research threshold. Do not record example values as measured outcomes.

For planned Unitree G1 EDU test sessions, include the exact hardware/EDU
variant, installed actuator and sensor configuration, calibration, firmware/SDK
versions, robot description/model revision, coordinate frames and safety-check
receipt. A manufacturer model name alone does not establish reproducibility.

Keep a complete environment record: OS, Python, dependencies, simulator version,
robot firmware, sensor settings and calibration where applicable.
A rerun must preserve inputs, pairing and scoring, then regenerate the same tables
within declared numerical tolerances. Report hardware-sensitive timing separately.
Implementation gaps and future cross-study extensions are tracked in
[Issue #16](https://github.com/MatPomGit/arc-rvi/issues/16) and the
[project state](project-state.md).
