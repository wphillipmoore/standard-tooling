"""Validate published documentation against markdown standards.

Scope: published documentation only — ``docs/site/**/*.md`` and ``README.md``.

Files under ``docs/site/`` receive markdownlint only (site navigation
handles ToC/H1).  ``README.md`` files receive markdownlint plus
structural checks (exactly one H1, a Table of Contents heading, no
heading-level skips).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path


def _classify_files(
    args: list[str],
) -> tuple[list[str], list[str]]:
    """Classify files into lint-only and structural-check groups.

    Returns ``(lint_files, struct_files)``.
    """
    lint_files: list[str] = []
    struct_files: list[str] = []

    if args:
        for arg in args:
            path = Path(arg)
            if not path.is_file():
                continue
            posix = path.as_posix()
            if posix.startswith("docs/site/") and posix.endswith(".md"):
                lint_files.append(arg)
            elif path.name == "README.md":
                struct_files.append(arg)
    else:
        site_dir = Path("docs/site")
        if site_dir.is_dir():
            lint_files = [str(p) for p in site_dir.rglob("*.md")]
        readme = Path("README.md")
        if readme.is_file():
            struct_files = ["README.md"]

    return lint_files, struct_files


def _run_markdownlint(files: list[str]) -> bool:
    """Run markdownlint on *files*. Return True if it passes."""
    cmd: list[str] = ["markdownlint"]
    config = Path(".markdownlint.yaml")
    if config.is_file():
        cmd.extend(["--config", str(config)])
    cmd.extend(files)
    result = subprocess.run(cmd, check=False)  # noqa: S603, S607
    return result.returncode == 0


_CODE_FENCE_RE = re.compile(r"^(```|~~~)")
_TOC_RE = re.compile(r"^## Table of Contents\s*$")
_HEADING_RE = re.compile(r"^(#{1,6}) ")


def _structural_check(file_path: str) -> bool:
    """Run structural checks on a standalone document. Return True if it passes."""
    in_code = False
    toc_found = False
    h1_count = 0
    last_level = 0
    errors: list[str] = []

    lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    for line_num, line in enumerate(lines, start=1):
        if _CODE_FENCE_RE.match(line):
            in_code = not in_code

        if in_code:
            continue

        if _TOC_RE.match(line):
            toc_found = True

        m = _HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            if level == 1:
                h1_count += 1
            if last_level > 0 and level > last_level + 1:
                errors.append(
                    f"ERROR: Heading level skips from {last_level} to {level} "
                    f"({file_path}:{line_num})"
                )
            last_level = level

    if h1_count != 1:
        errors.append(f"ERROR: expected exactly one H1 heading, found {h1_count} ({file_path})")

    if not toc_found:
        errors.append(f"ERROR: missing ## Table of Contents ({file_path})")

    for error in errors:
        print(error, file=sys.stderr)

    return len(errors) == 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    lint_files, struct_files = _classify_files(args)
    all_files = lint_files + struct_files

    if not all_files:
        return 0

    if not shutil.which("markdownlint"):
        print("FATAL: markdownlint not found on PATH", file=sys.stderr)
        return 2

    markdownlint_ok = _run_markdownlint(all_files)

    struct_ok = True
    for file_path in struct_files:
        if not _structural_check(file_path):
            struct_ok = False

    return 0 if (markdownlint_ok and struct_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
