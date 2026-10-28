"""Read-only local photometric ROI evaluation for annotated vehicle photographs.

The tool does not recognize cars, command the robot or judge defect visibility.
Photo assets are never uploaded, installed, or modified by this script.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rvi.vehicle_image_quality import analyze_capture, compare_pair


def _no_duplicates(items):
    result = {}
    for k, v in items:
        if k in result:
            raise ValueError(f"duplicate JSON field: {k}")
        result[k] = v
    return result


def _invalid_constant(value):
    raise ValueError(f"invalid nonfinite JSON value: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads(
            args.manifest.read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=_invalid_constant,
        )
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
        mode = manifest.get("mode")
        if mode == "single":
            result = analyze_capture(manifest.get("capture"), args.data_root)
        elif mode == "pair":
            result = compare_pair(manifest.get("before"), manifest.get("after"),
                                  args.data_root)
        else:
            raise ValueError("mode must be single or pair")
    except (ValueError, OSError, TypeError, UnicodeError) as exc:
        print(f"vehicle ROI audit failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
