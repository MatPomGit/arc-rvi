# Research software

ARC-RVI is independent research software for reproducible robotic visual inspection. It covers target localization, viewpoint planning, coverage evaluation and image-quality assessment. Defect classification is outside the scope.

## Installation and offline examples

Python 3.11 or newer is required.

```bash
python -m pip install -e .
python scripts/validate.py
rvi plan --scenario simulation/scenarios/inspection_small.json --output results/plan.json
rvi benchmark --suite simulation/suites/fixture_smoke.json --output results/benchmark.json
rvi simulate --scene simulation/worlds/planar_inspection.json --output results/simulation.json
```

Run these commands from the cloned repository. See [architecture](docs/architecture.md), [benchmark](docs/benchmark.md), [localization](docs/localization.md) and [simulation](docs/simulation.md) for detailed interfaces and limitations.

## Evidence and limitations

The software operates on deterministic fixtures and planar geometric simulations, with exploratory synthetic studies. Unitree G1 EDU is a reference platform; the physical adapter is not configured. Synthetic results do not establish physical safety or confirm hypotheses.

See the [research programme](experiments/README.md), [reproducibility contract](docs/reproducibility.md) and [safety requirements](docs/safety.md).
