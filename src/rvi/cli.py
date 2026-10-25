"""Offline command-line baseline for synthetic inspection view planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import Viewpoint
from .viewpoints import plan_viewpoints


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rvi")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="plan candidate views from a synthetic JSON scenario")
    plan.add_argument("--scenario", required=True, type=Path)
    plan.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = make_parser().parse_args(argv)
    if arguments.command == "plan":
        scenario = json.loads(arguments.scenario.read_text(encoding="utf-8"))
        views = [
            Viewpoint(
                identifier=entry["id"],
                x=entry["x"],
                y=entry["y"],
                visible_regions=tuple(entry["regions"]),
            )
            for entry in scenario["viewpoints"]
        ]
        plan = plan_viewpoints(
            views,
            scenario["required_regions"],
            tuple(scenario.get("start_xy", [0.0, 0.0])),
        )
        payload = {
            "evidence_type": "synthetic_fixture",
            "planner": "greedy_distance_penalized_baseline",
            "viewpoint_ids": plan.viewpoint_ids,
            "covered_regions": plan.covered_regions,
            "travel_distance_m": round(plan.travel_distance_m, 6),
        }
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
