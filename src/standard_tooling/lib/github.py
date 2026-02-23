"""GitHub CLI (``gh``) subprocess wrappers."""

from __future__ import annotations

import subprocess


def run(*args: str) -> None:
    """Run a gh command and raise on failure."""
    subprocess.run(("gh", *args), check=True)  # noqa: S603, S607


def read_output(*args: str) -> str:
    """Run a gh command and return stripped stdout."""
    result = subprocess.run(  # noqa: S603, S607
        ("gh", *args), check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def create_pr(*, base: str, title: str, body_file: str) -> str:
    """Create a pull request and return its URL."""
    return read_output("pr", "create", "--base", base, "--title", title, "--body-file", body_file)


def auto_merge(ref: str, *, strategy: str, delete_branch: bool = True) -> None:
    """Enable auto-merge on a PR.

    *strategy* must be ``--squash``, ``--merge``, or ``--rebase``.
    """
    cmd = ["pr", "merge", "--auto", strategy, ref]
    if delete_branch:
        cmd.append("--delete-branch")
    run(*cmd)
