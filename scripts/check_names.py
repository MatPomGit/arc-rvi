"""Optional local content guard using a private, external denylist.

The denylist must never be committed to this repository. Each nonempty line
contains a token whose appearance should cause validation to fail.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def scan_text_files(paths: list[Path], tokens: list[str]) -> list[tuple[str, int]]:
    failures = []
    normalized = [token.casefold() for token in tokens if token.strip()]
    for path in paths:
        try:
            contents = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(contents.splitlines(), 1):
            if any(token in line.casefold() for token in normalized):
                failures.append((path.as_posix(), line_number))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--denylist",
        type=Path,
        default=Path(os.environ["RVI_DENYLIST_PATH"])
        if "RVI_DENYLIST_PATH" in os.environ else None,
        help="path to an untracked token list outside the repository",
    )
    args = parser.parse_args(argv)
    if args.denylist is None or not args.denylist.is_file():
        print("External denylist required; no repository changes made.", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[1]
    denylist = args.denylist.resolve(strict=True)
    if denylist == root or root in denylist.parents:
        print("Denylist must be outside the repository.", file=sys.stderr)
        return 2
    tokens = [line.strip() for line in denylist.read_text(encoding="utf-8").splitlines()]
    tokens = [line for line in tokens if line and not line.startswith("#")]
    if not tokens:
        print("Nonempty external denylist required.", file=sys.stderr)
        return 2

    proc = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    tracked = [
        item.decode("utf-8") for item in proc.stdout.split(bytes([0])) if item
    ]
    # The pre-existing legal text is not project-authored and must be preserved.
    paths = [root / item for item in tracked if item != "LICENSE"]
    failures = scan_text_files(paths, tokens)
    for filename, line_number in failures:
        print(f"Disallowed token detected at {filename}:{line_number}")
    if failures:
        return 1
    print(f"PASS: {len(paths)} tracked files scanned against external denylist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
