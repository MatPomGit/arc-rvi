"""Offline planning, paired comparison and geometric inspection simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters.simulator import run_simulation
from .benchmark import run_benchmark
from .conditions import generate_conditions
from .experiment import run_experiment
from .localization import run_localization_fixture, run_sensor_localization
from .image_dataset import evaluate_image_manifest
from .localization_population import (generate_localization_population,
                                      analyze_localization_population)
from .pilot import analyze_pilot
from .planning import plan_family_sample
from .power_mc import analyze_cluster_monte_carlo
from .robot_model import inspect_urdf
from .population import generate_population
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
    benchmark.add_argument("--sensor", type=Path,
                           help="exploratory simulation only; hides geometry truth from policies")
    benchmark.add_argument("--output", required=True, type=Path)
    simulate = sub.add_parser("simulate", help="evaluate a route in a planar geometric scene")
    simulate.add_argument("--scene", required=True, type=Path)
    simulate.add_argument("--output", required=True, type=Path)
    conditions = sub.add_parser("conditions", help="generate paired study01 geometric scenes and split manifests")
    conditions.add_argument("--spec", required=True, type=Path)
    conditions.add_argument("--output-dir", required=True, type=Path)
    localize = sub.add_parser("localize", help="evaluate synthetic instance-assignment fixtures")
    localize_input = localize.add_mutually_exclusive_group(required=True)
    localize_input.add_argument("--fixture", type=Path)
    localize_input.add_argument("--sensor-study", type=Path)
    localize_input.add_argument("--population-manifest", type=Path)
    localize_input.add_argument("--image-manifest", type=Path)
    localize.add_argument("--partition", choices=("development", "pilot"), default="pilot")

    localize.add_argument("--output", required=True, type=Path)
    localize_population = sub.add_parser("localize-population", help="generate P02 grouped synthetic object sets")
    localize_population.add_argument("--spec", required=True, type=Path)
    localize_population.add_argument("--output-dir", required=True, type=Path)
    pilot = sub.add_parser("pilot", help="analyze exploratory study01 paired geometric pilot")
    pilot.add_argument("--manifest", required=True, type=Path)
    pilot.add_argument("--output", required=True, type=Path)
    pilot.add_argument("--reference", default="fixed_order", choices=("fixed_order", "greedy_coverage", "greedy_distance"))
    pilot.add_argument("--comparator", default="greedy_distance", choices=("fixed_order", "greedy_coverage", "greedy_distance"))
    pilot.add_argument("--seed", type=int, default=20261026)
    population = sub.add_parser("population", help="sample exploratory geometry families for study01")
    population.add_argument("--spec", required=True, type=Path)
    population.add_argument("--output-dir", required=True, type=Path)
    precision = sub.add_parser("precision", help="assumption-only independent-family sample size sensitivity")
    precision.add_argument("--spec", required=True, type=Path)
    precision.add_argument("--output", required=True, type=Path)
    precision.add_argument("--pilot-summary", type=Path)
    batch = sub.add_parser("batch", help="replay exploratory study01 batches with immutable receipts")
    batch_source = batch.add_mutually_exclusive_group(required=True)
    batch_source.add_argument("--manifest", type=Path)
    batch_source.add_argument("--suite", type=Path, help="fixture-only suite; never physical or holdout")
    batch.add_argument("--partition", default="pilot", choices=("development", "pilot"))
    batch.add_argument("--output-dir", required=True, type=Path)
    batch.add_argument("--resume", action="store_true", help="verify existing outputs without modifying them")
    cluster_mc = sub.add_parser("power-mc", help="exploratory family-level Monte Carlo power and CI diagnostics")
    cluster_mc.add_argument("--spec", required=True, type=Path)
    cluster_mc.add_argument("--output", required=True, type=Path)
    robot_model = sub.add_parser("robot-model",
                                 help="audit hash-pinned local URDF without robot I/O")
    robot_model.add_argument("--urdf", required=True, type=Path)
    robot_model.add_argument("--expected-sha256", required=True)
    robot_model.add_argument("--camera-frame")
    robot_model.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "localize":
            if arguments.output.exists():
                raise ValueError("output already exists; choose a new path")
            payload = (run_localization_fixture(arguments.fixture)
                       if arguments.fixture is not None else
                       run_sensor_localization(arguments.sensor_study)
                       if arguments.sensor_study is not None else
                       analyze_localization_population(arguments.population_manifest,
                                                       partition=arguments.partition)
                       if arguments.population_manifest is not None else
                       evaluate_image_manifest(arguments.image_manifest,
                                               partition=arguments.partition))
            serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                    indent=2, allow_nan=False) + "\n"
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            with arguments.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
            print(f"Saved {payload['evidence_type']} localization report to {arguments.output}")
            return 0
        if arguments.command == "localize-population":
            manifest = generate_localization_population(arguments.spec, arguments.output_dir)
            print(f"Saved {len(manifest['records'])} grouped P02 synthetic study cases")
            return 0
        if arguments.command == "batch":
            receipt = run_experiment(manifest=arguments.manifest, suite=arguments.suite,
                                     partition=arguments.partition,
                                     output_dir=arguments.output_dir, resume=arguments.resume)
            print(f"Verified experiment batch {receipt['provenance']['run_id']} in {arguments.output_dir}")
            return 0
        if arguments.command == "population":
            manifest = generate_population(arguments.spec, arguments.output_dir)
            print(f"Saved {len(manifest['scenes'])} exploratory population scenes to {arguments.output_dir}")
            return 0
        if arguments.command == "conditions":
            manifest = generate_conditions(arguments.spec, arguments.output_dir)
            print(f"Saved {len(manifest['scenes'])} exploratory scenes to {arguments.output_dir}")
            return 0
        if arguments.command in ("benchmark", "simulate", "pilot", "precision",
                                 "power-mc", "robot-model"):
            if arguments.output.exists():
                raise ValueError("output already exists; choose a new path")
            if arguments.command == "robot-model":
                payload = inspect_urdf(arguments.urdf, arguments.expected_sha256,
                                       camera_frame=arguments.camera_frame)
            elif arguments.command == "pilot":
                payload = analyze_pilot(arguments.manifest, arguments.reference,
                                        arguments.comparator, seed=arguments.seed)
            elif arguments.command == "precision":
                payload = plan_family_sample(arguments.spec, arguments.pilot_summary)
            elif arguments.command == "power-mc":
                payload = analyze_cluster_monte_carlo(arguments.spec)
            else:
                payload = (run_benchmark(arguments.suite, arguments.sensor)
                           if arguments.command == "benchmark"
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
