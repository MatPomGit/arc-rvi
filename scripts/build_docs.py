"""Prepare the public MkDocs source tree from canonical repository files.

The staging tree is disposable; scientific protocols remain in experiments/.
No source files are rewritten, downloaded, or interpreted as code.
"""
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".build" / "mkdocs-src"


def main() -> None:
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    sources: list[Path] = [
        ROOT / "index.md",
        ROOT / "README.md",
        ROOT / "AUTOPILOT_PLAN.md",
        ROOT / "PROJECT_STATE.yaml",
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "docs").rglob("*.css")),
        *sorted((ROOT / "experiments").rglob("*.md")),
        *sorted((ROOT / "papers").glob("paper*/manuscript.tex")),
    ]
    for path in sources:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"invalid documentation source: {path}")
        relative = path.relative_to(ROOT)
        target = DEST / relative.as_posix()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    print(f"Staged {len(sources)} canonical public documentation files")


if __name__ == "__main__":
    main()
