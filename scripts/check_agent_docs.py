"""Offline, standard-library audit of agent instructions and canonical documents.

No network, secret access, hardware I/O or modification of repository files.
Checks local Markdown destinations, AGENTS workflow structure and version drift.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

DOCUMENTS = (
    "AGENTS.md",
    "index.md",
    "README.md",
    "AUTOPILOT_PLAN.md",
    "docs/architecture.md",
    "docs/methodology.md",
    "docs/reproducibility.md",
    "docs/safety.md",
    "docs/project-state.md",
    "docs/website.md",
    "docs/glossary.md",
    "docs/teaching-standards.md",
    "docs/development/agent-workflow.md",
    "docs/development/coding-standards.md",
    "docs/development/testing.md",
    "docs/development/writing-standards.md",
    "experiments/README.md",
    "experiments/analysis/README.md",
)

LINK = re.compile(r"!?\[[^\]\n]+\]\(([^)\n]+)\)")
MAIN_SECTIONS = ("I. Zasady projektu", "II. Procedura pracy agenta")
REQUIRED_RULES = (
    "adapter: not_configured",
    "fixture",
    "simulation",
    "physical",
    "PROJECT_STATE.yaml",
    "python scripts/validate.py",
    "python scripts/build_docs.py",
    "docs/development/agent-workflow.md",
    "docs/development/coding-standards.md",
    "docs/development/testing.md",
    "docs/development/writing-standards.md",
    "docs/teaching-standards.md",
    "docs/glossary.md",
    "DoR",
    "DoD",
    "python -m mkdocs build --strict",
)
VERSION = re.compile(r"(?m)^  software_version:\s*['\"]?([^'\"\s#]+)")


def inspect_agent_structure(content: str) -> list[str]:
    """Reject missing workflow steps, core safety gates and malformed structure."""
    issues = []
    sections = re.findall(r"^## (.+)$", content, flags=re.MULTILINE)
    if sections != list(MAIN_SECTIONS):
        issues.append("AGENTS.md: expected exactly the two canonical main sections")
    steps = re.findall(r"^### Krok (\d+)\.", content, flags=re.MULTILINE)
    if steps != [str(n) for n in range(1, 9)]:
        issues.append("AGENTS.md: expected steps 1 through 8 in order")
    count = len(content.splitlines())
    if len(content.encode("utf-8")) >= 32 * 1024:
        issues.append("AGENTS.md: size must be below 32 KiB")
    if not 100 <= count <= 200:
        issues.append(f"AGENTS.md: expected 100..200 lines, got {count}")
    for rule in REQUIRED_RULES:
        if rule not in content:
            issues.append(f"AGENTS.md: missing required contract: {rule}")
    return issues


def inspect_agent_scenarios(content: str) -> list[str]:
    """Check that the operational document covers each of twenty cases."""
    actual = re.findall(
        r"^\|\s*(\d{2})\s+[^|]*\|[^|]+\|\s*$",
        content,
        flags=re.MULTILINE,
    )
    expected = [f"{index:02}" for index in range(1, 21)]
    if actual != expected:
        return ["agent-workflow.md: expected scenarios 01 through 20 in order"]
    return []


def inspect_user_text(content: str) -> list[str]:
    """Reject typographic dashes in newly authored project instructions."""
    if "\u2013" in content or "\u2014" in content:
        return ["New agent and development documents must avoid U+2013/U+2014"]
    return []


def inspect_links(root: Path, documents: tuple[str, ...]) -> list[str]:
    """Resolve local Markdown link destinations inside the repository only."""
    base = root.resolve()
    issues = []
    for name in documents:
        source = base / name
        if not source.is_file():
            issues.append(f"{name}: missing canonical document")
            continue
        for line_number, line in enumerate(
            source.read_text(encoding="utf-8").splitlines(), 1
        ):
            for found in LINK.finditer(line):
                destination = found.group(1).strip().split(maxsplit=1)[0]
                destination = destination.strip("<>")
                if not destination or destination.startswith("#"):
                    continue
                url = urlsplit(destination)
                if url.scheme or url.netloc:
                    continue  # Remote resources need separate online verification.
                path = unquote(url.path)
                if not path:
                    continue
                # The site publishes root README.md under a non-reserved name.
                # Check the canonical source, not the generated site path.
                if name == "index.md" and path == "project-readme.md":
                    path = "README.md"
                resolved = (source.parent / path).resolve()
                try:
                    resolved.relative_to(base)
                except ValueError:
                    issues.append(
                        f"{name}:{line_number}: link escapes repository: {path}"
                    )
                    continue
                if not resolved.is_file():
                    issues.append(
                        f"{name}:{line_number}: missing link target: {path}"
                    )
    return issues


def inspect_version(pyproject: str, state: str) -> list[str]:
    """Compare package version with the canonical research state without YAML dependencies."""
    try:
        package = tomllib.loads(pyproject)["project"]["version"]
    except (KeyError, tomllib.TOMLDecodeError) as error:
        return [f"pyproject.toml: cannot read project.version: {error}"]
    matches = VERSION.findall(state)
    if len(matches) != 1:
        return ["PROJECT_STATE.yaml: expected one repository.software_version"]
    if matches[0] != package:
        return [
            "PROJECT_STATE.yaml: software_version "
            f"{matches[0]} differs from pyproject.toml {package}"
        ]
    return []


def audit(root: Path) -> list[str]:
    """Return all actionable errors; do not alter any files."""
    issues = inspect_links(root, DOCUMENTS)
    agent_file = root / "AGENTS.md"
    if agent_file.is_file():
        issues.extend(
            inspect_agent_structure(agent_file.read_text(encoding="utf-8"))
        )
    workflow = root / "docs" / "development" / "agent-workflow.md"
    if workflow.is_file():
        issues.extend(
            inspect_agent_scenarios(workflow.read_text(encoding="utf-8"))
        )
    for name in (
        "AGENTS.md",
        "docs/development/agent-workflow.md",
        "docs/development/coding-standards.md",
        "docs/development/testing.md",
        "docs/development/writing-standards.md",
        "docs/teaching-standards.md",
        "docs/glossary.md",
    ):
        source = root / name
        if source.is_file():
            issues.extend(inspect_user_text(source.read_text(encoding="utf-8")))
    pyproject = root / "pyproject.toml"
    state = root / "PROJECT_STATE.yaml"
    if not pyproject.is_file() or not state.is_file():
        issues.append("Missing pyproject.toml or PROJECT_STATE.yaml")
    else:
        issues.extend(
            inspect_version(
                pyproject.read_text(encoding="utf-8"),
                state.read_text(encoding="utf-8"),
            )
        )
    return issues


def main() -> int:
    """Print explicit reproducible status and return a failing exit code on drift."""
    problems = audit(ROOT)
    for problem in problems:
        print(f"[FAIL] {problem}", file=sys.stderr)
    if problems:
        print(f"[DONE] FAIL: {len(problems)} consistency violations")
        return 1
    print(
        f"[DONE] PASS: {len(DOCUMENTS)} documents, agent workflow and "
        "package/state versions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
