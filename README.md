# Autonomous Robotic Visual Inspection (RVI)

Independent research software for autonomous perception, mobile inspection, viewpoint planning and reproducible image acquisition. The initial platform of interest is a humanoid robot, but algorithms and experiments should remain hardware- and object-agnostic.

## Scope

- Target identification and localization in multi-object scenes.
- Safe navigation, view selection and coverage planning.
- Image acquisition, quality assurance and evidence provenance.
- Repeatable simulation and physical experiments, statistical analysis and publications.
- Export of neutral images and metadata to external analytical systems. Defect classification is **out of scope**.

## Repository map

- `src/rvi/`: shared research library; hardware adapters are separate.
- `config/`: neutral configuration templates, not device credentials.
- `simulation/`: scenario fixtures and future simulator environments.
- `experiments/exp01_...exp08_/`: eight independent research protocols.
- `papers/paper01/...paper08/`: manuscripts and citation material.
- `datasets/`: data governance; large/raw/private datasets live outside Git.
- `tests/`: offline unit, integration and fixture checks.
- `docs/`: architecture, methodology, safety and reproducibility.

## Offline start

Requires Python 3.11+; core tooling uses the standard library.

```bash
python -m pip install -e .
python scripts/validate.py
rvi plan --scenario simulation/scenarios/inspection_small.json --output results/plan.json
rvi benchmark --suite simulation/suites/fixture_smoke.json --output results/benchmark.json
```

The `plan` command operates on a **synthetic fixture**, not a real robot or physics simulator. It provides a reproducible baseline greedy coverage planner, not an optimality claim. Real robot and simulator integrations are intentionally not implemented yet.

The [paired benchmark](docs/benchmark.md) compares three deterministic planning methods
and records partial coverage, route length, failures and source/input hashes.

## Research integrity

No client identities, proprietary data, credentials, real vehicle identifiers, raw imagery or confidential project documents are committed. Any article using external material must first clear its publication and licensing rights. Existing source code is subject to the repository's `LICENSE`; manuscript rights and third-party content must be reviewed separately.

## Research development

Start with the [research program](experiments/README.md), then read the study-specific
protocol and [shared analysis plan](experiments/analysis/README.md).
The [project state](docs/project-state.md) lists implemented features and the next work package.

For contribution rules, see `AGENTS.md`.
