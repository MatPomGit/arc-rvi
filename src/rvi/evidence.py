"""Path-safe content hashes and image metadata for research provenance."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess

from pathlib import Path

from . import __version__


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_image_manifest(run_directory: Path, image_paths: list[Path]) -> list[dict]:
    root = run_directory.resolve(strict=True)
    records = []
    seen: set[str] = set()
    for image_path in image_paths:
        candidate = Path(image_path)
        if candidate.is_symlink():
            raise ValueError("symlinked images are not supported")
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file():
            raise ValueError("each image must be a regular file")
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("image must be inside run directory") from exc
        name = relative.as_posix()
        if name in seen:
            raise ValueError("duplicate image path")
        seen.add(name)
        records.append({
            "relative_path": name,
            "size_bytes": resolved.stat().st_size,
            "sha256": sha256_file(resolved),
        })
    return sorted(records, key=lambda record: record["relative_path"])


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def software_provenance() -> dict:
    """Hash executed package sources, including local edits and untracked modules."""
    package = Path(__file__).resolve().parent
    hashes = {path.relative_to(package).as_posix(): digest(path.read_bytes())
              for path in sorted(package.rglob("*.py"))}
    snapshot = digest(json.dumps(hashes, sort_keys=True).encode("utf-8"))
    root = package.parents[1]
    commit = None
    dirty = None
    # Installed packages need not have a Git checkout. Do not report another repo.
    if (root / ".git").exists():
        try:
            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(root), *args], check=True, capture_output=True,
                    timeout=5, text=True).stdout.strip()
            commit = git("rev-parse", "HEAD")
            dirty = bool(git("status", "--porcelain", "--untracked-files=normal"))
        except (OSError, subprocess.SubprocessError):
            commit = None
            dirty = None
    return {"commit_sha": commit, "dirty_tree": dirty,
            "package_source_sha256": snapshot, "package_files": hashes,
            "package_version": __version__, "python": platform.python_version(),
            "platform": platform.system()}
