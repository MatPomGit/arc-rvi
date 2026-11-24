"""Stage only explicitly authorized publication sources."""
from __future__ import annotations

import re
import shutil
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".build" / "mkdocs-src"
MANIFEST = "website/public-sources.txt"
INTERNAL = re.compile(
    r"\b(?:agent(?:s|a|em|owi|om|ach|ami|ów|ow\w*)?|agenci|agencie|agentk(?:a|i|ę|ą|o|om|ami|ach)|agentek|autopilot\w*|"
    r"homeserver|andromeda|codex|chatgpt|github approval|exact.sha|commented|"
    r"DoR|DoD)\b|AGENTS\.md|agent-workflow|AUTOPILOT_PLAN|"
    r"docs/development/|PROJECT_STATE\.yaml",
    re.IGNORECASE,
)
ALLOWED_SUFFIXES = {".md", ".css", ".tex"}


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or ".." in path.parts
            or "\\" in value or path.as_posix() != value
            or path.suffix not in ALLOWED_SUFFIXES):
        raise ValueError(f"Invalid publication path: {value}")
    if INTERNAL.search(value):
        raise ValueError(f"Non-public publication path: {value}")
    return path


def publication_sources(root: Path) -> dict[str, str]:
    """Return destination-to-source mapping, rejecting unsafe or duplicate paths."""
    result = {}
    for raw in (root / MANIFEST).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        source, separator, destination = line.partition("|")
        if not separator:
            raise ValueError("Malformed publication manifest")
        source_path = safe_relative(source.strip())
        dest_path = safe_relative(destination.strip())
        if not (source_path.parts[0] in {"docs", "experiments", "papers"}
                or source_path.parts[:2] == ("website", "content")):
            raise ValueError(f"Non-public source directory: {source_path}")
        if (source_path.parts[:2] == ("docs", "development")
                or str(source_path) in {"docs/website.md", "docs/teaching-standards.md",
                                        "docs/project-state.md", "docs/research/reproducibility.md",
                                        "docs/reproducibility.md"}):
            raise ValueError(f"Non-public source: {source_path}")
        if str(dest_path) in result:
            raise ValueError(f"Duplicate publication destination: {dest_path}")
        result[str(dest_path)] = str(source_path)
    if "index.md" not in result:
        raise ValueError("Publication manifest has no homepage")
    return result


def checked_content(root: Path, name: str) -> str:
    path = root / name
    if not path.is_file() or any((root.joinpath(*PurePosixPath(name).parts[:i])).is_symlink()
                                 for i in range(1, len(PurePosixPath(name).parts) + 1)):
        raise ValueError(f"Invalid publication source: {name}")
    content = path.read_text(encoding="utf-8")
    if INTERNAL.search(content):
        raise ValueError(f"Non-public operational content in {name}")
    return content


def main() -> None:
    if DEST.is_symlink() or DEST.parent.is_symlink():
        raise ValueError("Publication destination is a symlink")
    if DEST.exists():
        shutil.rmtree(DEST)
    sources = publication_sources(ROOT)
    contents = {dest: checked_content(ROOT, source) for dest, source in sources.items()}
    DEST.mkdir(parents=True)
    for dest, content in contents.items():
        target = DEST / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print(f"Staged {len(sources)} authorized publication files")


if __name__ == "__main__":
    main()
