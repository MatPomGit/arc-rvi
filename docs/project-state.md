# Project state

[PROJECT_STATE.yaml](../PROJECT_STATE.yaml) is the canonical machine-readable status.
[AUTOPILOT_PLAN.md](../AUTOPILOT_PLAN.md) defines portfolio work packages.
The [study index](../experiments/README.md) owns scientific protocol and publication boundaries.

The software version is defined in `pyproject.toml`.
The `repository.software_version` field in `PROJECT_STATE.yaml` must match it;
`python scripts/check_agent_docs.py` enforces this relationship.
Historical verification receipts and their exact SHAs remain historical records;
do not rewrite them when the current package or instructions change.

The root `AGENTS.md` governs agent decisions. Current Issues and PRs
rather than historical next-action hints determine the active work queue.
The [documentation build guide](website.md) describes CI checks and review gates.
