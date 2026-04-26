"""Validation checks that run inside a dev container.

Called by ``validate-local-common`` via ``docker-test``.  Runs:
  1. Repository profile validation
  2. Markdown standards validation
  3. shellcheck on all shell scripts under ``scripts/``
  4. yamllint on YAML files under ``.github/`` and ``docs/`` (issue #302)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from standard_tooling.bin import markdown_standards, repo_profile_cli
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


_YAML_EXTS = frozenset({".yml", ".yaml"})
_YAML_SKIP_DIRS = frozenset({".worktrees", ".venv", ".venv-host", "node_modules"})


def _find_yaml_files(repo_root: Path) -> list[str]:
    """Discover YAML files we care about: workflows, issue templates,
    repo-root config files (.markdownlint.yaml etc.), and
    docs/site/mkdocs.yml. Skips vendored / venv / worktree paths.
    The yamllint config lives at the repo root (`.yamllint`).
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

    # Filter out anything that wandered into a skipped subtree.
    filtered: list[str] = []
    for f in files:
        rel_parts = set(Path(f).relative_to(repo_root).parts)
        if rel_parts & _YAML_SKIP_DIRS:
            continue
        filtered.append(f)
    return sorted(set(filtered))


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
