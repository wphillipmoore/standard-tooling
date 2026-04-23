"""Git subprocess wrappers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run(*args: str) -> None:
    """Run a git command and raise on failure."""
    subprocess.run(("git", *args), check=True)  # noqa: S603, S607


def read_output(*args: str) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(  # noqa: S603, S607
        ("git", *args), check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def repo_root() -> Path:
    """Return the repository root directory."""
    return Path(read_output("rev-parse", "--show-toplevel"))


def is_main_worktree() -> bool:
    """Return True when the CWD belongs to the main worktree.

    Secondary worktrees have a ``.git`` file whose git-dir points into
    ``.git/worktrees/<name>/``, while the main worktree's git-dir is
    ``.git`` itself — ``--git-dir`` and ``--git-common-dir`` are equal
    only for the main worktree.
    """
    git_dir = Path(read_output("rev-parse", "--git-dir")).resolve()
    common_dir = Path(read_output("rev-parse", "--git-common-dir")).resolve()
    return git_dir == common_dir


def current_branch() -> str:
    """Return the current branch name."""
    return read_output("rev-parse", "--abbrev-ref", "HEAD")


def has_staged_changes() -> bool:
    """Return True if there are staged changes."""
    result = subprocess.run(  # noqa: S603, S607
        ("git", "diff", "--cached", "--quiet"), check=False
    )
    return result.returncode != 0


def ref_exists(ref: str) -> bool:
    """Return True if a git ref exists."""
    result = subprocess.run(  # noqa: S603, S607
        ("git", "rev-parse", "--verify", "--quiet", ref), check=False
    )
    return result.returncode == 0


def merged_branches(target: str) -> list[str]:
    """Return local branches merged into *target*."""
    output = read_output("branch", "--merged", target, "--format=%(refname:short)")
    if not output:
        return []
    return output.splitlines()
