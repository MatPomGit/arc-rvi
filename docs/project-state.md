# Project state

Updated: 2026-10-26

## Implemented

- Standard-library planar greedy coverage planner and synthetic `rvi plan` command
- Mission transition and quality-threshold helpers, path-safe image hashes
- 23 offline tests passing on the initial code revision `521756961946bd0eff4618c328c43d38071574cc`
- Eight prospective protocols, shared analysis plan and publication boundaries, version 1.1.0

## Unresolved scientific gates

No collected research dataset, physics adapter or physical robot adapter is implemented.
Protocol thresholds, sample-size calculations, comparator implementations and immutable
confirmation splits remain open. The manuscript files are templates.
Literature and novelty review remain open; the protocols contain proposed design choices,
not literature-backed claims of method superiority.

## Next work package

Implement study 01's fixture-level paired benchmark runner and trial records in the
shared library. Keep a single CLI command and standard-library dependencies.
Start with fixed-order, coverage-only greedy and distance-penalized greedy baselines.
Record actual selected views, coverage, travel and failures, including impossible scenes.
Use explicit fixture evidence labels and source/configuration hashes.
Verify pairing, deterministic reruns and scoring against hand-calculable scenes.
Do not interpret these fixtures as a physics benchmark.

Estimated software work before a simulation pilot: 3 to 5 coherent PRs for the runner,
validated simulator adapter, reference scoring, baselines and pilot analysis.
Physical readiness depends on equipment access and calibration; no reliable PR count
can be assigned yet.

Verification command: `python scripts/validate.py`.
