# Paired fixture benchmark

Application version: 1.4.0

## Run

After the editable installation described in the README, run:

```bash
rvi benchmark --suite simulation/suites/fixture_smoke.json --output results/benchmark.json
```

The command writes one JSON report and prints its location. Choose a new output path
for each saved report; existing files are never overwritten. Invalid input exits with
code 2 and a short error. Recorded algorithm failures are benchmark outcomes and do
not make the command fail. No robot connection or additional dependency is required.

## Methods and scoring

Every method receives the same candidates, visibility labels, initial position and
travel budget. Each declared scenario is evaluated once per method.

| Method | Selection rule | Tie rule |
| --- | --- | --- |
| `fixed_order` | Visit the input shot list, including redundant views, until coverage is complete | Input order |
| `greedy_coverage` | Select the largest number of uncovered required regions | Ascending viewpoint ID |
| `greedy_distance` | Maximize new-region count divided by `(1 + distance_m)` | Larger gain, then smaller distance, then ascending ID |

The additive constant in the distance score represents a fixed one-metre reference
scale inherited from the original baseline. Changing coordinate units changes this score.
Greedy methods skip views with no coverage gain. They do not solve a global route problem.
All methods stop if their chosen next move exceeds the remaining budget; they do not
substitute another view at that point. The original `rvi plan` API retains its complete-plan
behaviour and raises an error when full coverage is impossible.

Coverage is the fraction of distinct required region labels visited. Regions have equal
weight and supplied visibility is treated as exact. This is not measured image quality
or mesh-area coverage. Distance is the sum of planar segments from the declared start;
there is no return leg, collision check, capture cost or timing model.

A move at the exact travel limit is accepted. A rejected move acquires no view and adds
no partial distance. Preserve all earlier accepted views on failure.
`unreachable_regions` means the method exhausted its useful candidates before full
coverage. `distance_budget_exceeded` means its next selected view was beyond the budget.
Both use `status: algorithm_failure`, with separate reason codes.

## Inputs

The suite uses schema version `1.0.0`. It specifies a unique technical suite ID,
`evidence_type: fixture`, a finite nonnegative `max_travel_distance_m` and a nonempty
list of scenario paths relative to the suite file. Paths may use `..` to reference
shared scenario directories. Duplicate files or scenario IDs are rejected.

Scenarios declare `scenario_id`, `evidence_type`, `required_regions`, `viewpoints` and
optional `start_xy` (default `[0, 0]`). Coordinates are metres. Required regions and
viewpoint IDs must be unique. Each viewpoint lists `id`, `x`, `y` and nonempty `regions`.
All visible regions must be declared in `required_regions`. An empty viewpoint list
is permitted to test an impossible task. Unknown fields, repeated JSON keys, non-finite
coordinates, boolean coordinates and invalid evidence labels are rejected.
The legacy scenario label `synthetic_fixture` is accepted only as an explicit fixture alias.

## Report and provenance

`trials` contains selected view IDs, covered and missing regions, distance, status and
reason for every method/scenario pair. `summary` includes every trial in each denominator,
including failures. Means give scenarios equal weight; they are descriptive software
checks, with no confidence intervals or population-level inference.

`inputs` hashes the actual suite and scenario bytes using SHA-256. `source` records
the package version, Python version, platform, package source-file hashes and aggregate
source hash. A source checkout also supplies the commit and dirty-tree status when Git
is available. Otherwise those two fields are null. Package hashes include untracked
Python modules; a commit alone must not be used to identify a dirty implementation.
Keep the corresponding source snapshot if a report will be archived.

`run_id` identifies the input/provenance specification, not an independent repetition.
Reports contain no wall-clock timestamps or random seed: these methods use no randomness.
For unchanged inputs and provenance, report bytes reproduce exactly. A changed commit,
dirty-tree flag, runtime or source hash can change `run_id` without changing the numerical
outcomes. Use the ignored `results/` directory to avoid an output file changing Git status.
This fixture format implements a subset of the [research run contract](reproducibility.md);
experimental timestamps, grouping, calibration and stochastic streams remain future work.

## Included checks

The smoke suite contains three hand-checkable cases. One has complete coverage;
one places a two-region view beyond the ten-metre budget while two nearby views
remain feasible; one makes the roof unreachable. The distance-aware method succeeds
in two of three cases; the other methods in one of three. These deliberately constructed
cases verify scoring and failure accounting. They do not estimate comparative research
performance or provide confirmation data for study 01.

## Paired geometric simulation

```bash
rvi benchmark --suite simulation/suites/geometric_smoke.json --output results/geometric.json
```

A simulation suite declares `schema_version: 1.0.0`, a `suite_id`,
`evidence_type: simulation` and a nonempty `scenes` list of relative world paths.
Each world's route is the common ordered candidate set, not a prescribed executed path.
All three policies use the same start, camera, obstacles, surface patches and time budget.
Candidate IDs follow input order. Duplicate scene IDs or files are rejected.

Visibility is derived from the [geometric model](simulation.md), not supplied region labels.
This baseline exposes known reference geometry to every method and reports
`visibility_access: known_geometry_oracle`. It does not evaluate perception of an
unknown surface. Greedy gains count uncovered patch IDs; distance scoring uses metres.
The final metric weights acquired patches by declared area, not by the planner's count.
Rotation and capture time are enforced by the simulator but are not in the greedy score.

Only accepted acquisitions contribute coverage. Methods stop at full coverage or their
first rejected action; exhausted candidates yield `unreachable_regions`.
`completed` in these trial records means all patches were acquired, unlike the supplied-route
execution status of `rvi simulate`. Summary denominators include failed trials.
Reports retain per-scene hashes, actual observations, partial coverage, time and distance.
The included far-first scene verifies a known budget trade-off, not comparative research merit.
The [seeded condition generator](conditions.md) now emits exploratory geometry
families, matched nominal/occluded conditions and disjoint development/pilot/holdout
suites with SHA-256 manifests. It provides no inferential analysis or frozen
confirmation dataset.
