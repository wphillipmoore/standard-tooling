"""Tests for standard_tooling.lib.github."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from standard_tooling.lib import github


def _completed(returncode: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout)


def test_run_delegates_to_subprocess() -> None:
    with patch("standard_tooling.lib.github.subprocess.run") as mock_run:
        mock_run.return_value = _completed()
        github.run("pr", "list")
    mock_run.assert_called_once_with(("gh", "pr", "list"), check=True)


def test_read_output_returns_stripped_stdout() -> None:
    with patch("standard_tooling.lib.github.subprocess.run") as mock_run:
        mock_run.return_value = _completed(stdout="  result\n")
        assert github.read_output("pr", "view") == "result"
    mock_run.assert_called_once_with(
        ("gh", "pr", "view"), check=True, text=True, capture_output=True
    )


def test_create_pr_returns_url() -> None:
    with patch("standard_tooling.lib.github.read_output", return_value="https://github.com/pr/1"):
        url = github.create_pr(base="main", title="title", body_file="body.md")
    assert url == "https://github.com/pr/1"


def test_wait_for_checks_passes_pr_ref() -> None:
    with patch("standard_tooling.lib.github.run") as mock_run:
        github.wait_for_checks("https://github.com/pr/1")
    mock_run.assert_called_once_with(
        "pr", "checks", "https://github.com/pr/1", "--watch", "--fail-fast"
    )


def test_merge_with_delete_branch() -> None:
    with patch("standard_tooling.lib.github.run") as mock_run:
        github.merge("https://github.com/pr/1", strategy="merge")
    mock_run.assert_called_once_with(
        "pr", "merge", "--merge", "https://github.com/pr/1", "--delete-branch"
    )


def test_merge_without_delete_branch() -> None:
    with patch("standard_tooling.lib.github.run") as mock_run:
        github.merge("https://github.com/pr/1", strategy="squash", delete_branch=False)
    mock_run.assert_called_once_with("pr", "merge", "--squash", "https://github.com/pr/1")


def test_list_project_repos() -> None:
    with patch(
        "standard_tooling.lib.github.read_output",
        return_value="acme/repo-b\nacme/repo-a\nacme/repo-a\n",
    ):
        repos = github.list_project_repos("acme", "5")
    assert repos == ["acme/repo-a", "acme/repo-b"]


def test_list_project_repos_empty() -> None:
    with patch(
        "standard_tooling.lib.github.read_output",
        return_value="",
    ):
        assert github.list_project_repos("acme", "5") == []
