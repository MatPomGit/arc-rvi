"""Path-safe content hashes and image metadata for research provenance."""

from __future__ import annotations

import hashlib
from pathlib import Path


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
