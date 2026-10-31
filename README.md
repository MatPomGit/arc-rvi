# Autonomous Robotic Visual Inspection (RVI)

Independent research software for reproducible robotic visual inspection: target localization, viewpoint planning, coverage evaluation and photographic quality assessment. The reference platform is a humanoid robot; the current executable tools are offline, and the shared algorithms remain hardware-agnostic.

**Primary use case:** photographing a specified car or part (e.g. rear bumper) despite specular reflections, then returning for operator-confirmed handoff. The [mission contract](docs/vehicle-inspection-missions.md) is evaluated offline on synthetic fixtures; live robot integration and physical trials are not implemented.


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
- `experiments/exp01_...exp08_/`: eight prospective research protocols, not completed studies.
- `papers/paper01/...paper08/`: candidate manuscripts and citation material, not publication evidence.
- `datasets/`: data governance; large/raw/private datasets live outside Git.
- `tests/`: offline unit, integration and fixture checks.
- `docs/`: architecture, methodology, safety and reproducibility.

## Verified software versus prospective research

| Component | Current scope | Not established |
| --- | --- | --- |
| `rvi plan`, `rvi benchmark`, `rvi simulate` | Deterministic fixtures and planar geometry/kinematics | Calibrated physics, physical coverage or robot safety |
| `rvi localize`, image-quality utilities | Synthetic proxies, offline PGM crops, supplied masks and bounded quality checks | General natural-image recognition or measured camera calibration |
| `rvi robot-model`, `rvi stance` | Source-hashed URDF, limited FK/collision-proxy and static support preflight | Certified full-body collision, dynamic balance or locomotion |
| Car/bumper inspection mission | Fixture-only identity, required-view, glare and return/handoff evaluation | Live target detection, autonomous photographs or safe physical return |
| P01-P08 research | Protocol drafts, exploratory synthetic analyses and publication scaffolds | Confirmatory evidence, physical field trials or submitted papers |

**Physical motion remains disabled.** `config/robot.yaml` retains
`adapter: not_configured`; `src/rvi/adapters/robot.py` rejects device operations.
Read [hardware safety gates](docs/safety.md) before any authorized hardware work.
For implementation details, see [architecture](docs/architecture.md),
[reproducibility](docs/reproducibility.md) and
[prospective study protocols](experiments/README.md).

## Offline start

Requires Python 3.11+; core package runtime uses the standard library.

```bash
python -m pip install -e .
python scripts/validate.py
python scripts/check_agent_docs.py
rvi plan --scenario simulation/scenarios/inspection_small.json --output results/plan.json
rvi benchmark --suite simulation/suites/fixture_smoke.json --output results/benchmark.json
rvi simulate --scene simulation/worlds/planar_inspection.json --output results/simulation.json
rvi benchmark --suite simulation/suites/geometric_smoke.json --output results/geometric.json
rvi benchmark --suite simulation/suites/geometric_smoke.json --sensor simulation/conditions/sensor_exploratory.json --output results/observed.json
rvi conditions --spec simulation/conditions/study01_pilot.json --output-dir results/study01_conditions
rvi localize --fixture simulation/suites/localization_fixture.json --output results/localization.json
rvi localize-population --spec simulation/conditions/study02_population_pilot.json --output-dir results/study02_population
rvi localize-population --spec simulation/conditions/study02_image_pilot.json --output-dir results/study02_images
rvi localize --population-manifest results/study02_images/manifest.json --partition pilot --output results/study02_image_pilot.json
# Optional operator-supplied offline PGM dataset, not included in Git:
# rvi localize --image-manifest /local/private_study02/manifest.json --partition pilot --output results/study02_local_images.json
rvi localize --population-manifest results/study02_population/manifest.json --partition pilot --output results/study02_pilot.json
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
The [offline Study 02 PGM reader](docs/localization.md) accepts operator-supplied
8-bit grayscale image crops, hashed references and split evaluator annotations;
no dataset is bundled and no camera calibration or physical result is implied.
The [synthetic grayscale Study 02 pilot](docs/localization.md) extends
association from 1D bearing/range proxies to generated 8×8 grayscale pixel
arrays with controlled appearance similarity and simulated-session noise;
no real camera images or calibrated 3D pose references are used.
The [grouped P02 synthetic pilot](docs/localization.md) compares fixed
bearing/range methods across separately seeded object-set families, paired
visibility and distractor separation conditions, with no confirmation claims.
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

## Development and validation

`AGENTS.md` defines the autonomous workflow, required safety gates, Issue
selection and PR integration procedure. Start with existing Issues and PRs,
not a copied list of tasks. The [architecture](docs/architecture.md),
[methodology](docs/methodology.md) and [research state](docs/project-state.md)
are the canonical entry points for relevant details.

All PRs run the offline test matrix (Python 3.11, 3.12 and 3.13).
Documentation CI also executes `python scripts/check_agent_docs.py`
and a strict MkDocs build. This checks local documentation links, the agent
workflow and package/version consistency; it does **not** verify external
citations or physically validate a robot. Review and branch protection
requirements are documented in the [build and governance guide](docs/website.md).
Do not mistake successful CI for independent scientific or safety review.

## Research development

Start with the [research program](experiments/README.md) and
[literature evidence gates](docs/literature.md), then read the study-specific
protocol and [shared analysis plan](experiments/analysis/README.md).
The canonical [project state](PROJECT_STATE.yaml) lists current evidence and next actions.
The [ARC plan](AUTOPILOT_PLAN.md) defines its portfolio role and proposed sensor interfaces.

Technical documentation build and publication instructions are maintained in
[Documentation build](docs/website.md).

For contribution and autonomous-agent rules, read the root `AGENTS.md`.
The agent [operating procedure](docs/development/agent-workflow.md) covers
Issues, concurrent tasks, DoR/DoD, exact-SHA CI, deployment and cleanup.
Before implementation consult [coding conventions](docs/development/coding-standards.md)
and [testing guidance](docs/development/testing.md); for prose consult
[writing standards](docs/development/writing-standards.md) and the
[scientific glossary](docs/glossary.md). [Teaching rules](docs/teaching-standards.md)
apply only when student materials are specifically requested.

The MkDocs site follows the system light/dark preference. It does not yet
include rendered LaTeX manuscript previews; source manuscripts remain drafts.

Kryteria dowodów badawczych: [reprodukowalność](docs/research/reproducibility.md), zasady w głównym `AGENTS.md`.
