#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""List every placeholder that still needs a real fact.

Finds {{< todo >}}...{{< /todo >}} shortcodes in content files and "TODO (" notes in
hugo.toml and README.md, and prints them as path:line: text. It only reports: it always
exits 0, so the site can be built and merged while drafts are still being rewritten.

Usage:
    uv run scripts/list_todos.py            # content/, hugo.toml, README.md
    uv run scripts/list_todos.py some/dir   # just these paths
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = [ROOT / "content", ROOT / "hugo.toml", ROOT / "README.md"]
SHORTCODE = re.compile(r"\{\{<\s*todo\s*>\}\}(.*?)\{\{<\s*/todo\s*>\}\}")
PLAIN = re.compile(r"TODO \(.*")


def files_under(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_dir():
            out.extend(sorted(f for f in p.rglob("*") if f.suffix in {".md", ".toml"}))
        elif p.exists():
            out.append(p)
    return out


def find_todos(paths: list[Path]) -> list[tuple[Path, int, str]]:
    """Every placeholder in the given files, as (path, line number, text)."""
    found = []
    for path in files_under(paths):
        in_code = False
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            # Examples inside fenced code blocks (as in the README) are not placeholders.
            if path.suffix == ".md" and line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            prose = re.sub(r"`[^`]*`", "", line)  # inline code is an example, not a placeholder
            hits = [m.group(1).strip() for m in SHORTCODE.finditer(prose)] if path.suffix == ".md" else []
            if not hits and (m := PLAIN.search(line)):
                hits = [m.group(0).strip()]
            found.extend((path, n, h) for h in hits)
    return found


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    paths = [Path(a) for a in args] or DEFAULT_PATHS
    todos = find_todos(paths)
    for path, n, text in todos:
        shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        print(f"{shown}:{n}: {text}")
    print(f"{len(todos)} TODO(s) left")
    return 0


if __name__ == "__main__":
    sys.exit(main())
