"""Offline predicted camera-view ranking; no robot or camera controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rvi.photometric_view import select_view


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    args = parser.parse_args()
    try:
        spec = json.loads(args.scenario.read_text(encoding="utf-8"))
        result = select_view(spec)
    except (OSError, ValueError, TypeError) as exc:
        print(f"predicted-view error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "candidate_selected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
