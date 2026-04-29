"""Run markdownlint on published documentation.

Scope: ``docs/site/**/*.md`` and ``README.md``.

Structural checks (H1 count, ToC, heading-level skips) live in
``repo_profile_cli`` as of issue #389.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _find_files() -> list[str]:
    """Discover published markdown files from CWD."""
    files: list[str] = []
    site_dir = Path("docs/site")
    if site_dir.is_dir():
        files.extend(str(p) for p in site_dir.rglob("*.md"))
    readme = Path("README.md")
    if readme.is_file():
        files.append(str(readme))
    return sorted(files)


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    files = _find_files()
    if not files:
        return 0

    if not shutil.which("markdownlint"):
        print("FATAL: markdownlint not found on PATH", file=sys.stderr)
        return 2

    cmd: list[str] = ["markdownlint"]
    config = Path(".markdownlint.yaml")
    if config.is_file():
        cmd.extend(["--config", str(config)])
    cmd.extend(files)
    result = subprocess.run(cmd, check=False)  # noqa: S603, S607
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
