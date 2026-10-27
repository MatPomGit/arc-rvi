# Autonomous Robotic Visual Inspection (RVI)

Independent research software for autonomous perception, mobile inspection, viewpoint planning and reproducible image acquisition. The initial platform of interest is a humanoid robot, but algorithms and experiments should remain hardware- and object-agnostic.

## Scope

- Target identification and localization in multi-object scenes.
- Safe navigation, view selection and coverage planning.
- Image acquisition, quality assurance and evidence provenance.
- Repeatable simulation and physical experiments, statistical analysis and publications.
- Export of neutral images and metadata to external analytical systems. Defect classification is **out of scope**.

**Reference test robot:** Unitree G1 EDU. This is a declared research-platform
choice, not an implemented robot integration or confirmation of available
hardware. The exact EDU variant, sensor payload and firmware must be verified
before importing a robot model or conducting physical tests. Shared algorithms
remain hardware-independent. An [offline URDF preflight](docs/architecture.md)
can check versioned link/joint topology and zero-pose camera frames without
connecting to a robot; see `config/robot.yaml`
and [physical test safety gates](docs/safety.md).

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
rvi benchmark --suite simulation/suites/geometric_smoke.json --sensor simulation/conditions/sensor_exploratory.json --output results/observed.json
rvi conditions --spec simulation/conditions/study01_pilot.json --output-dir results/study01_conditions
rvi localize --fixture simulation/suites/localization_fixture.json --output results/localization.json
rvi pilot --manifest results/study01_conditions/manifest.json --output results/study01_pilot_analysis.json
rvi population --spec simulation/conditions/study01_population_pilot.json --output-dir results/study01_population
rvi population --spec simulation/conditions/study01_factorial_pilot.json --output-dir results/study01_factorial
rvi pilot --manifest results/study01_population/manifest.json --output results/study01_population_analysis.json
rvi precision --spec simulation/conditions/study01_precision_sensitivity.json --output results/study01_precision.json
rvi batch --suite simulation/suites/fixture_smoke.json --output-dir results/study01_fixture_batch
rvi power-mc --spec simulation/conditions/study01_cluster_mc.json --output results/study01_cluster_mc.json
```

The `plan` command operates on a **synthetic fixture**, not a real robot or physics simulator. It provides a reproducible baseline greedy coverage planner, not an optimality claim. Real robot and external physics-engine integrations remain unavailable.

The optional [observation-driven benchmark](docs/benchmark.md) compares
fixed-order, distance-only and past-feature parallax heuristics without passing
reference geometry to the policy; the example is exploratory software QA only.
The [paired benchmark](docs/benchmark.md) compares three deterministic planning methods
and records partial coverage, route length, failures and source/input hashes.
The [planar simulator](docs/simulation.md) computes visibility, swept-footprint collision
and model time from a geometric scene and a supplied route.
The [seeded condition generator](docs/conditions.md) creates separate exploratory
geometry families and matched nominal/occluded scenes with a SHA-256 manifest.
The [exploratory paired pilot analysis](docs/pilot-analysis.md) checks input hashes,
retains failed trials and summarizes family-paired effects without claiming confirmation.
The [exploratory population sampler](docs/population.md) draws distinct synthetic
geometry families with disjoint partitions, paired nominal/occluded conditions,
and a separately versioned balanced 12-cell geometry/occlusion/light/clutter matrix;
it does not establish an independent physical sampling frame.
The [sample-size sensitivity planner](docs/sample-size.md) computes illustrative
independent-family counts from explicit SD, effect, precision and missingness
assumptions; it is not a frozen confirmatory design.
The [cluster Monte Carlo tool](docs/cluster-monte-carlo.md) explores synthetic
null rejection, interval coverage and assumed alternative power at the
**family** level under normal/heavy-tailed effects and missingness stress.
The [exploratory P02 sensor association](docs/localization.md) reuses the
existing selector on generated bearing/range detections with separate
evaluator-only truth; actual appearance recognition is not implemented.
The [planar feature sensor](docs/simulation.md) provides reusable, seeded
horizontal camera observations with evaluator-only geometric truth. It is
uncalibrated and does not change the known-geometry benchmark.
The [immutable experiment batch interface](docs/experiment-batches.md) stores
paired trial records, independent-unit metadata and provenance receipts for
exploratory Study 01. It blocks holdout access and does not cover physical studies.

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

Documentation is published at https://matpomgit.github.io/arc-rvi/.
See [publication instructions](docs/website.md) and the
[Study 02 localization specification](docs/localization.md).
The initial deployment is verified by GitHub Actions run 40418374958;
future changes must pass the strict site build before release.
