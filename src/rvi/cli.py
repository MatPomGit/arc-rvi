"""Offline command-line baseline for synthetic inspection view planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_benchmark
from .scenarios import load_scenario
from .viewpoints import plan_viewpoints


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rvi")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="plan candidate views from a synthetic JSON scenario")
    plan.add_argument("--scenario", required=True, type=Path)
    plan.add_argument("--output", required=True, type=Path)
    benchmark = sub.add_parser("benchmark", help="compare three methods on paired fixtures")
    benchmark.add_argument("--suite", required=True, type=Path)
    benchmark.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "benchmark":
            if arguments.output.exists():
                raise ValueError("output already exists; choose a new path")
            payload = run_benchmark(arguments.suite)
            serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    indent=2, allow_nan=False) + "\n"
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also prevents a late overwrite of an input or result.
            with arguments.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
            print(f"Saved {len(payload['trials'])} fixture trials to {arguments.output}")
            return 0
        if arguments.command == "plan":
            scenario, _ = load_scenario(arguments.scenario)
            plan = plan_viewpoints(scenario.viewpoints, scenario.required_regions, scenario.start_xy)
            payload = {
                "evidence_type": "synthetic_fixture",
                "planner": "greedy_distance_penalized_baseline",
                "viewpoint_ids": plan.viewpoint_ids,
                "covered_regions": plan.covered_regions,
                "travel_distance_m": round(plan.travel_distance_m, 6),
            }
            if arguments.output.resolve() == arguments.scenario.resolve():
                raise ValueError("output must differ from the input scenario")
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2,
                           allow_nan=False), encoding="utf-8")
            return 0
    except (OSError, ValueError, UnicodeError, OverflowError) as exc:
        parser.error(str(exc))
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
