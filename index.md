# Autonomous Robotic Visual Inspection

ARC-RVI develops reproducible, hardware-independent research tools for
robotic visual inspection: target identification, viewpoint selection,
coverage assessment and acquisition quality. The current executable
workflows operate offline with synthetic fixtures and exploratory simulations.

**Physical robot control is not implemented.** Unitree G1 EDU is a reference
platform for future, separately authorized tests. Simulation results do
not establish physical safety or confirm scientific hypotheses.

## Explore the documentation

| Area | Start here |
| --- | --- |
| Research programme | [Eight prospective studies](experiments/README.md) and [shared analysis](experiments/analysis/README.md) |
| Software and models | [System architecture](docs/architecture.md), [simulator limits](docs/simulation.md) and [benchmark](docs/benchmark.md) |
| Scientific integrity | [Methodology](docs/methodology.md), [reproducibility](docs/reproducibility.md) and [physical safety](docs/safety.md) |
| Project status | [Current scientific state](docs/project-state.md), [roadmap](AUTOPILOT_PLAN.md) and [complete README](README.md) |

## Main research scenario

The reference mission is to photograph a specified vehicle or component,
including reflective bodywork, and return for operator-confirmed handoff.
The [mission specification](docs/vehicle-inspection-missions.md) currently
defines an offline evaluation, not a verified autonomous physical mission.

## Working with the software

The [complete repository README](README.md) contains the installation
instructions, command examples and scope of implemented tools. For
engineering changes, consult the [agent workflow](docs/development/agent-workflow.md)
and [validation rules](docs/development/testing.md).

The source code and ongoing development are hosted in
[MatPomGit/arc-rvi](https://github.com/MatPomGit/arc-rvi).
