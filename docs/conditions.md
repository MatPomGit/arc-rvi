# Seeded geometric scene conditions (study 01)

This package generates an **exploratory software pilot**, not a confirmatory
scientific dataset. No imagery, illumination model, clutter sensor or physical
robot data is generated. The evaluated planners have known-geometry oracle
visibility. The only paired challenge is a geometric line-of-sight occluder.

## Reproduce

Python 3.11+ and the standard library suffice:

```bash
rvi conditions --spec simulation/conditions/study01_pilot.json --output-dir results/study01_conditions
rvi benchmark --suite results/study01_conditions/suites/development.json --output results/study01_development.json
rvi benchmark --suite results/study01_conditions/suites/pilot.json --output results/study01_pilot.json
rvi pilot --manifest results/study01_conditions/manifest.json --output results/study01_pilot_analysis.json
```

The generator refuses an existing output directory. Delete an **unneeded**
output yourself or choose a new one; it will not silently replace evidence.
`results/` is ignored by Git. Do not use the `holdout` suite for method tuning.
Its existence in this public repository does not make it blinded or frozen.

## Design

The specification fixes one master seed, three computational replicates per
family, and two conditions (`nominal`, `occluded`). Six template-level geometry
families (two-, three- and four-patch spatial arrangements) are assigned **once**
across `development`, `pilot` and `holdout`. This prevents identical families
from crossing partitions. Replicate seeds are derived from a stable SHA-256
mapping of master seed, family and replicate index, independent of iteration
order. Both conditions of a pair use the same sampled patch geometry and
candidate poses; only the obstacle list differs. A candidate-line occluder
has the sole intended challenge effect. Poses and outcomes remain subject to
the planar simulator's time, collision and visibility constraints.

Every file is canonical sorted-key JSON with a terminal newline. The
`manifest.json` lists partition, family, pairing ID, replicate seed, condition,
exact scene-byte SHA-256, source generator hash and original specification
hash. Three per-partition suite files directly fit `rvi benchmark`; the manifest
also hashes those suites. A method comparison is paired by `scene_id` and a
condition comparison by `pair_id` within a geometry family. Neither the 18
pairs nor the six families constitute a defensible sample-size justification.

## Interpretation and limitations

This design tests code pathways for reproducible scenarios, reporting and
partition discipline. It neither implements illumination or clutter factors
required by the prospective study protocol nor validates a physical sensor.
Geometry families are chosen by hand; perturbations do not make them an
independent population sample. The [pilot analyzer](pilot-analysis.md)
validates paired provenance and performs descriptive family-level contrasts. Even the `holdout` partition is preliminary:
freeze thresholds, sampling rules and baseline versions **before** opening
confirmation data. Retain failures and perform family-clustered uncertainty
analysis only after that protocol is finalized. See the
[study protocol](../experiments/exp01_benchmark/protocol.md) and
[simulation model](simulation.md).
