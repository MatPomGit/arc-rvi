"""Read-only colour-cue triage for annotated cars in a local image.

It never performs object detection, automatic natural-language grounding or
physical robot actions. Output is advisory and always requires confirmation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rvi.vehicle_colour_cues import propose_colour_targets


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _no_nonfinite(value):
    raise ValueError(f"nonfinite input constant: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"),
                          object_pairs_hook=_unique_keys,
                          parse_constant=_no_nonfinite)
        report = propose_colour_targets(data, args.data_root)
    except (ValueError, OSError, TypeError, UnicodeError) as exc:
        print(f"colour-cue analysis failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
