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


def wait_for_checks(pr: str) -> None:
    """Block until all required checks on ``pr`` complete; fail fast on the first red.

    Surfaces the failure via ``subprocess.CalledProcessError`` — callers are
    responsible for deciding how to react (the release-workflow convention is
    to stop and surface; do not retry).
    """
    run("pr", "checks", pr, "--watch", "--fail-fast")


def merge(pr: str, *, strategy: str, delete_branch: bool = True) -> None:
    """Merge a PR synchronously (without ``--auto``).

    ``strategy`` is one of ``"merge"``, ``"squash"``, ``"rebase"`` — passed
    through as ``--merge``, ``--squash``, ``--rebase``.
    """
    cmd = ["pr", "merge", f"--{strategy}", pr]
    if delete_branch:
        cmd.append("--delete-branch")
    run(*cmd)


def list_project_repos(owner: str, project: str) -> list[str]:
    """Return sorted, unique repos linked to a GitHub Project."""
    jq_filter = (
        f".[] | select(.projectsV2.Nodes | length > 0) "
        f"| select(.projectsV2.Nodes[].number == {project}) "
        f"| .nameWithOwner"
    )
    output = read_output(
        "repo",
        "list",
        owner,
        "--json",
        "nameWithOwner,projectsV2",
        "--limit",
        "100",
        "--jq",
        jq_filter,
    )
    return sorted({r for r in output.splitlines() if r})
