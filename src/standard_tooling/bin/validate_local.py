"""Shared driver for pre-PR local validation.

Reads primary_language from docs/repository-standards.md, then runs:
  1. validate-local-common   (always)
  2. validate-local-<lang>   (if primary_language is set and script exists)
  3. validate-local-custom   (if exists -- repo-specific escape hatch)
"""

from __future__ import annotations

import shutil
import subprocess
import sys

from standard_tooling.lib import git, repo_profile


def _run_validator(name: str) -> bool:
    """Run a PATH-based validator script. Return True on success."""
    path = shutil.which(name)
    if path is None:
        return True  # Not found means skip
    print(f"Running: {name}")
    result = subprocess.run((path,), check=False)  # noqa: S603
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    root = git.repo_root()

    try:
        profile = repo_profile.read_profile(root)
        primary_language = profile.primary_language
    except FileNotFoundError:
        primary_language = ""

    print("=" * 40)
    print("st-validate-local")
    print(f"primary_language: {primary_language or '<not set>'}")
    print("=" * 40)
    print()

    if not _run_validator("validate-local-common"):
        return 1

    if primary_language and primary_language != "none":
        print()
        if not _run_validator(f"validate-local-{primary_language}"):
            return 1

    if shutil.which("validate-local-custom"):
        print()
        if not _run_validator("validate-local-custom"):
            return 1

    print()
    print("=" * 40)
    print("st-validate-local: all checks passed")
    print("=" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main())
