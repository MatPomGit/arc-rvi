"""Audit the actual rendered publication tree before uploading it."""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote

try:
    from scripts.build_docs import INTERNAL, ROOT
except ModuleNotFoundError:
    from build_docs import INTERNAL, ROOT


class PublicHTML(HTMLParser):
    """Collect rendered text and references, excluding runtime script/style code."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        for name, value in attrs:
            if value and name in {"href", "src", "title", "alt", "aria-label", "content"}:
                self.parts.append(unquote(value))

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def audit(site: Path) -> list[str]:
    problems = []
    if not (site / "index.html").is_file():
        return ["Missing generated homepage"]
    index = site / "search" / "search_index.json"
    if not index.is_file():
        problems.append("Missing generated search index")
    for path in sorted(site.rglob("*")):
        relative = path.relative_to(site).as_posix()
        if path.is_symlink():
            problems.append(f"Symlink in generated site: {relative}")
            continue
        if INTERNAL.search(relative) or relative.startswith("docs/development/") or (
            relative.startswith(("docs/website/", "docs/teaching-standards/"))
        ):
            problems.append(f"Non-public output path: {relative}")
        if not path.is_file():
            continue
        if path.suffix == ".html":
            parser = PublicHTML()
            parser.feed(path.read_text(encoding="utf-8"))
            content = " ".join(parser.parts)
        elif path == index:
            data = json.loads(path.read_text(encoding="utf-8"))
            content = " ".join(
                str(doc.get(field, ""))
                for doc in data["docs"]
                for field in ("location", "title", "text")
            )
        elif path.suffix in {".tex", ".md", ".css"}:
            content = path.read_text(encoding="utf-8")
        else:
            continue
        if INTERNAL.search(unquote(content)):
            problems.append(f"Non-public content in generated file: {relative}")
    return problems


def main() -> int:
    problems = audit(ROOT / ".build" / "site")
    for problem in problems:
        print(f"[FAIL] {problem}", file=sys.stderr)
    if problems:
        return 1
    print("[PASS] Rendered publication boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
