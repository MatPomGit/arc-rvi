# Project state

Updated: 2026-10-26

## Implemented

- Standard-library planar greedy coverage planner and synthetic `rvi plan` command
- Mission transition and quality-threshold helpers, path-safe image hashes
- Application version 1.1.0: paired fixture benchmark with three deterministic baselines,
  partial outcomes, distance budgets, strict input validation and source/input hashes
- Application version 1.2.0 adds planar geometric simulation, visibility, swept-footprint
  collision checks, action timing, area-weighted patch coverage and `rvi simulate`
- 57 offline tests, including analytic geometry, partial outcomes and command replay
- Eight prospective protocols, shared analysis plan and publication boundaries, version 1.1.0

## Unresolved scientific gates

No collected research dataset, physics adapter or physical robot adapter is implemented.
Protocol thresholds, sample-size calculations, comparator implementations and immutable
confirmation splits remain open. The manuscript files are templates.
Literature and novelty review remain open; the protocols contain proposed design choices,
not literature-backed claims of method superiority.

## Next work package

Connect the three benchmark policies to geometric simulation without supplying
prelabelled visibility. Generate paired conditions with explicit seeds and disjoint
scene-family partitions. Preserve partial outcomes and use common time budgets.
Acceptance: methods receive the same scene and candidate poses; reports identify model,
conditions and source hashes, and reproduce analytic failure cases.
Then add independent geometry families and pilot analysis before confirmation.
An external physics engine remains a separate calibrated integration.

Estimated software work before a geometric simulation pilot: 2 to 3 coherent PRs for
paired condition generation, policy integration and pilot analysis.
Physical readiness depends on equipment access and calibration; no reliable PR count
can be assigned yet.

Verification command: `python scripts/validate.py`.
