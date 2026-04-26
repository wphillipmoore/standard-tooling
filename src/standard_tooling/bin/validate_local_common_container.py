"""Validation checks that run inside a dev container.

Called by ``validate-local-common`` via ``docker-test``.  Runs:
  1. Repository profile validation
  2. Markdown standards validation
  3. shellcheck on all shell scripts under ``scripts/``
"""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from standard_tooling.bin import markdown_standards, repo_profile_cli

if TYPE_CHECKING:
    from pathlib import Path
from standard_tooling.lib import git


def _find_shell_files(repo_root: Path) -> list[str]:
    """Discover shell files under scripts/."""
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.is_dir():
        return []

    files: list[str] = []
    for path in scripts_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".sh" or "git-hooks" in path.parts or "bin" in path.parts:
            files.append(str(path))
    return sorted(files)


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    repo_root = git.repo_root()

    print("Running: repo-profile")
    rc = repo_profile_cli.main()
    if rc != 0:
        return rc

    print("Running: markdown-standards")
    rc = markdown_standards.main()
    if rc != 0:
        return rc

    shell_files = _find_shell_files(repo_root)
    if shell_files:
        print(f"Running: shellcheck ({len(shell_files)} files)")
        result = subprocess.run(  # noqa: S603
            ["shellcheck", *shell_files],  # noqa: S607
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
