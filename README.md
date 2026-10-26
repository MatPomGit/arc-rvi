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
- `simulation/`: scenario fixtures and planar geometric worlds.
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
rvi simulate --scene simulation/worlds/planar_inspection.json --output results/simulation.json
rvi benchmark --suite simulation/suites/geometric_smoke.json --output results/geometric.json
rvi conditions --spec simulation/conditions/study01_pilot.json --output-dir results/study01_conditions
```

The `plan` command operates on a **synthetic fixture**, not a real robot or physics simulator. It provides a reproducible baseline greedy coverage planner, not an optimality claim. Real robot and external physics-engine integrations remain unavailable.

The [paired benchmark](docs/benchmark.md) compares three deterministic planning methods
and records partial coverage, route length, failures and source/input hashes.
The [planar simulator](docs/simulation.md) computes visibility, swept-footprint collision
and model time from a geometric scene and a supplied route.
The [seeded condition generator](docs/conditions.md) creates separate exploratory
geometry families and matched nominal/occluded scenes with a SHA-256 manifest.

## Research integrity

No client identities, proprietary data, credentials, real vehicle identifiers, raw imagery or confidential project documents are committed. Any article using external material must first clear its publication and licensing rights. Existing source code is subject to the repository's `LICENSE`; manuscript rights and third-party content must be reviewed separately.

## Research development

Start with the [research program](experiments/README.md), then read the study-specific
protocol and [shared analysis plan](experiments/analysis/README.md).
The canonical [project state](PROJECT_STATE.yaml) lists current evidence and next actions.
The [ARC plan](AUTOPILOT_PLAN.md) defines its portfolio role and proposed sensor interfaces.

For contribution rules, see `AGENTS.md`.


## Research documentation (MkDocs)

The canonical documentation can be assembled into a navigable MkDocs site
without duplicating the eight experiment protocols:

```bash
python -m pip install mkdocs==1.6.1
python scripts/build_docs.py
python -m mkdocs build --strict
```

The intended GitHub Pages URL is https://matpomgit.github.io/arc-rvi/.
See [site publication instructions](docs/website.md) and the
[Study 02 localization specification](docs/localization.md).
Public availability depends on enabling GitHub Actions as the Pages source
and observing a successful deploy; do not interpret the URL alone as proof.
