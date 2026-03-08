"""Shared driver for pre-PR local validation.

Reads primary_language from docs/repository-standards.md, then runs:
  1. validate-local-common   (always)
  2. validate-local-<lang>   (if primary_language is set and script exists)
  3. validate-local-custom   (if exists -- repo-specific escape hatch)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING

from standard_tooling.lib import git, repo_profile

if TYPE_CHECKING:
    from pathlib import Path


def _find_validator(name: str, scripts_bin: Path) -> str | None:
    """Locate a validator by *name*.

    Search order:
      1. ``st-{name}`` on PATH (installed entry point)
      2. The repository's own ``scripts/bin/`` directory
    """
    entry_point = shutil.which(f"st-{name}")
    if entry_point is not None:
        return entry_point
    local = scripts_bin / name
    if local.is_file() and os.access(local, os.X_OK):
        return str(local)
    return None


def _run_validator(name: str, scripts_bin: Path) -> bool:
    """Run a validator script. Return True on success, True (skip) if not found."""
    path = _find_validator(name, scripts_bin)
    if path is None:
        return True
    print(f"Running: {path}")
    result = subprocess.run((path,), check=False)  # noqa: S603
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    required = {"docker": ("docker",), "docker-test": ("st-docker-test",)}
    for tool, candidates in required.items():
        if not any(shutil.which(c) for c in candidates):
            print(f"ERROR: {tool} is required for local validation", file=sys.stderr)
            return 1

    root = git.repo_root()
    scripts_bin = root / "scripts" / "bin"

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

    if not _run_validator("validate-local-common", scripts_bin):
        return 1

    if primary_language and primary_language != "none":
        print()
        if not _run_validator(f"validate-local-{primary_language}", scripts_bin):
            return 1

    custom = _find_validator("validate-local-custom", scripts_bin)
    if custom is not None:
        print()
        if not _run_validator("validate-local-custom", scripts_bin):
            return 1

    print()
    print("=" * 40)
    print("st-validate-local: all checks passed")
    print("=" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main())
