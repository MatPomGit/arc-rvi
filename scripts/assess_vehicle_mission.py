"""Offline CLI to audit a supplied *synthetic* vehicle photograph mission trace."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rvi.vehicle_mission import assess_mission


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mission", type=Path, help="A fixture-only JSON mission log; never drives the robot")
    args = p.parse_args()
    try:
        payload = json.loads(args.mission.read_text(encoding="utf-8"))
        report = assess_mission(payload)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"mission validation error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["verdict"] == "fixture_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
