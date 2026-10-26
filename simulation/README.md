# Simulation and fixtures

`scenarios/` contains public synthetic input configurations.
`worlds/` is reserved for future reproducible simulator worlds.

A JSON scenario is **not** a physics simulation. The current planner assumes
known object visibility and planar coordinates; it does not prove safe motion.
Document simulator version, physics settings, geometry source, random seeds,
sensor noise and deviations from physical tests before publishing results.

`simulation/suites/fixture_smoke.json` pairs three hand-checkable scenarios across the
benchmark methods. See [benchmark inputs and scoring](../docs/benchmark.md).
