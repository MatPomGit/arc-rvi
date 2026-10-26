# Reproducibility contract

Version: 1.1.0

## Run and trial records

The following fields specify the proposed research record. No current CLI command
implements this complete contract. Keep private measurements and large assets outside Git.
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

Keep a complete environment record: OS, Python, dependencies, simulator version,
robot firmware, sensor settings and calibration where applicable.
A rerun must preserve inputs, pairing and scoring, then regenerate the same tables
within declared numerical tolerances. Report hardware-sensitive timing separately.
The next implementation is specified in [project state](project-state.md).
