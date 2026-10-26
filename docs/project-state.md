# Project state

Updated: 2026-10-26

## Implemented

- Standard-library planar greedy coverage planner and synthetic `rvi plan` command
- Mission transition and quality-threshold helpers, path-safe image hashes
- Application version 1.1.0: paired fixture benchmark with three deterministic baselines,
  partial outcomes, distance budgets, strict input validation and source/input hashes
- 40 offline tests, including paired scoring, provenance, replay and CLI errors
- Eight prospective protocols, shared analysis plan and publication boundaries, version 1.1.0

## Unresolved scientific gates

No collected research dataset, physics adapter or physical robot adapter is implemented.
Protocol thresholds, sample-size calculations, comparator implementations and immutable
confirmation splits remain open. The manuscript files are templates.
Literature and novelty review remain open; the protocols contain proposed design choices,
not literature-backed claims of method superiority.

## Next work package

Add study 01's simulator adapter and independently verified reference scoring.
Define a minimal scene, sensor and observation interface before selecting an engine.
Verify coordinate frames, surface visibility, collision and elapsed-time measurements
against analytic scenes. Keep fixture and physics evidence separate.
Then implement condition sampling, held-out geometry families and pilot analysis.

Estimated software work before a simulation pilot: 2 to 4 coherent PRs for the adapter,
reference scoring, simulator baselines and pilot analysis.
Physical readiness depends on equipment access and calibration; no reliable PR count
can be assigned yet.

Verification command: `python scripts/validate.py`.
