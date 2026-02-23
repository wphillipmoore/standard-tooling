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


def test_auto_merge_with_delete_branch() -> None:
    with patch("standard_tooling.lib.github.run") as mock_run:
        github.auto_merge("https://github.com/pr/1", strategy="--squash")
    mock_run.assert_called_once_with(
        "pr", "merge", "--auto", "--squash", "https://github.com/pr/1", "--delete-branch"
    )


def test_auto_merge_without_delete_branch() -> None:
    with patch("standard_tooling.lib.github.run") as mock_run:
        github.auto_merge("https://github.com/pr/1", strategy="--merge", delete_branch=False)
    mock_run.assert_called_once_with("pr", "merge", "--auto", "--merge", "https://github.com/pr/1")
