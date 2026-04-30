"""Common validation checks (container-local).

Runs inside the dev container via ``st-docker-run``:
  1. Repository profile validation (includes README structural checks)
  2. markdownlint on published markdown (docs/site/, README.md)
  3. shellcheck on all shell scripts under ``scripts/``
  4. yamllint on YAML files under ``.github/`` and ``docs/`` (issue #302)
"""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from standard_tooling.bin import repo_profile_cli
from standard_tooling.lib import git

if TYPE_CHECKING:
    from pathlib import Path


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


def _find_markdown_files(repo_root: Path) -> list[str]:
    """Discover published markdown files: docs/site/**/*.md and README.md."""
    files: list[str] = []

    site_dir = repo_root / "docs" / "site"
    if site_dir.is_dir():
        for path in site_dir.rglob("*.md"):
            files.append(str(path))

    readme = repo_root / "README.md"
    if readme.is_file():
        files.append(str(readme))

    return sorted(files)


_YAML_EXTS = frozenset({".yml", ".yaml"})


def _find_yaml_files(repo_root: Path) -> list[str]:
    """Discover YAML files we care about: repo-root config
    (.markdownlint.yaml etc.), `.github/` tree (workflows, issue
    templates), and `docs/site/mkdocs.yml`. The yamllint config lives
    at the repo root (`.yamllint`).

    Vendored paths (`.worktrees`, `.venv`, `.venv-host`,
    `node_modules`) are excluded by construction — discovery only
    walks the listed locations, never venv/worktree subtrees.
    """
    files: list[str] = []

    # Repo-root level YAML config files (e.g., .markdownlint.yaml).
    for path in repo_root.iterdir():
        if path.is_file() and path.suffix in _YAML_EXTS:
            files.append(str(path))

    # .github/ tree (workflows, issue templates, etc.).
    github_dir = repo_root / ".github"
    if github_dir.is_dir():
        for path in github_dir.rglob("*"):
            if path.is_file() and path.suffix in _YAML_EXTS:
                files.append(str(path))

    # docs/site/mkdocs.yml.
    mkdocs = repo_root / "docs" / "site" / "mkdocs.yml"
    if mkdocs.is_file():
        files.append(str(mkdocs))

    return sorted(set(files))


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    repo_root = git.repo_root()

    print("Running: repo-profile")
    rc = repo_profile_cli.main()
    if rc != 0:
        return rc

    md_files = _find_markdown_files(repo_root)
    if md_files:
        print(f"Running: markdownlint ({len(md_files)} files)")
        cmd: list[str] = ["markdownlint"]
        config = repo_root / ".markdownlint.yaml"
        if config.is_file():
            cmd.extend(["--config", str(config)])
        cmd.extend(md_files)
        result = subprocess.run(cmd, check=False)  # noqa: S603, S607
        if result.returncode != 0:
            return result.returncode

    shell_files = _find_shell_files(repo_root)
    if shell_files:
        print(f"Running: shellcheck ({len(shell_files)} files)")
        result = subprocess.run(  # noqa: S603
            ["shellcheck", *shell_files],  # noqa: S607
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    yaml_files = _find_yaml_files(repo_root)
    if yaml_files:
        print(f"Running: yamllint ({len(yaml_files)} files)")
        result = subprocess.run(  # noqa: S603
            ["yamllint", *yaml_files],  # noqa: S607
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
