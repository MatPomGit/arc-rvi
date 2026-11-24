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


# Structural boundaries separate words; inline markup must not split them.
BLOCK_TAGS = frozenset({
    "address", "article", "aside", "blockquote", "br", "caption", "dd",
    "details", "dialog", "div", "dl", "dt", "fieldset", "figcaption",
    "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section",
    "summary", "table", "tbody", "td", "th", "thead", "tfoot", "tr", "ul",
})


class PublicHTML(HTMLParser):
    """Collect rendered text and references, excluding runtime script/style code."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.references: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        if not self.skip and tag in BLOCK_TAGS:
            self.parts.append(" ")
        for name, value in attrs:
            if value and name in {"href", "src", "title", "alt", "aria-label", "content"}:
                self.references.append(value)

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1
        if not self.skip and tag in BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_fields(content: str) -> list[str]:
    """Preserve contiguous inline text and inspect references separately."""
    parser = PublicHTML()
    parser.feed(content)
    parser.close()
    return ["".join(parser.parts), *parser.references]


def search_fields(data: dict) -> list[str]:
    """Inspect plain index fields and any embedded HTML without joining records."""
    fields = []
    for doc in data["docs"]:
        for name in ("location", "title", "text"):
            value = str(doc.get(name, ""))
            fields.append(value)
            if name != "location":
                fields.extend(html_fields(value))
    return fields


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
            fields = html_fields(path.read_text(encoding="utf-8"))
        elif path == index:
            fields = search_fields(json.loads(path.read_text(encoding="utf-8")))
        elif path.suffix in {".tex", ".md", ".css"}:
            fields = [path.read_text(encoding="utf-8")]
        else:
            continue
        if any(INTERNAL.search(unquote(field)) for field in fields):
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
