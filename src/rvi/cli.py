"""Offline planning, paired comparison and geometric inspection simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters.simulator import run_simulation
from .benchmark import run_benchmark
from .conditions import generate_conditions
from .localization import run_localization_fixture
from .pilot import analyze_pilot
from .scenarios import load_scenario
from .viewpoints import plan_viewpoints


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rvi")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="plan candidate views from a synthetic JSON scenario")
    plan.add_argument("--scenario", required=True, type=Path)
    plan.add_argument("--output", required=True, type=Path)
    benchmark = sub.add_parser("benchmark", help="compare three methods on paired fixtures or geometric scenes")
    benchmark.add_argument("--suite", required=True, type=Path)
    benchmark.add_argument("--output", required=True, type=Path)
    simulate = sub.add_parser("simulate", help="evaluate a route in a planar geometric scene")
    simulate.add_argument("--scene", required=True, type=Path)
    simulate.add_argument("--output", required=True, type=Path)
    conditions = sub.add_parser("conditions", help="generate paired study01 geometric scenes and split manifests")
    conditions.add_argument("--spec", required=True, type=Path)
    conditions.add_argument("--output-dir", required=True, type=Path)
    localize = sub.add_parser("localize", help="evaluate synthetic instance-assignment fixtures")
    localize.add_argument("--fixture", required=True, type=Path)
    localize.add_argument("--output", required=True, type=Path)
    pilot = sub.add_parser("pilot", help="analyze exploratory study01 paired geometric pilot")
    pilot.add_argument("--manifest", required=True, type=Path)
    pilot.add_argument("--output", required=True, type=Path)
    pilot.add_argument("--reference", default="fixed_order", choices=("fixed_order", "greedy_coverage", "greedy_distance"))
    pilot.add_argument("--comparator", default="greedy_distance", choices=("fixed_order", "greedy_coverage", "greedy_distance"))
    pilot.add_argument("--seed", type=int, default=20261026)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "localize":
            if arguments.output.exists():
                raise ValueError("output already exists; choose a new path")
            payload = run_localization_fixture(arguments.fixture)
            serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    indent=2, allow_nan=False) + "\n"
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            with arguments.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
            print(f"Saved fixture localization report to {arguments.output}")
            return 0
        if arguments.command == "conditions":
            manifest = generate_conditions(arguments.spec, arguments.output_dir)
            print(f"Saved {len(manifest['scenes'])} exploratory scenes to {arguments.output_dir}")
            return 0
        if arguments.command in ("benchmark", "simulate", "pilot"):
            if arguments.output.exists():
                raise ValueError("output already exists; choose a new path")
            if arguments.command == "pilot":
                payload = analyze_pilot(arguments.manifest, arguments.reference,
                                        arguments.comparator, seed=arguments.seed)
            else:
                payload = (run_benchmark(arguments.suite) if arguments.command == "benchmark"
                           else run_simulation(arguments.scene))
            serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    indent=2, allow_nan=False) + "\n"
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also prevents a late overwrite of an input or result.
            with arguments.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
            print(f"Saved {payload['evidence_type']} report to {arguments.output}")
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
