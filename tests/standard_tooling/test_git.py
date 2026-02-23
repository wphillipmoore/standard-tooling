"""Tests for standard_tooling.lib.git."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from standard_tooling.lib import git


def _completed(returncode: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout)


def test_run_delegates_to_subprocess() -> None:
    with patch("standard_tooling.lib.git.subprocess.run") as mock_run:
        mock_run.return_value = _completed()
        git.run("status")
    mock_run.assert_called_once_with(("git", "status"), check=True)


def test_read_output_returns_stripped_stdout() -> None:
    with patch("standard_tooling.lib.git.subprocess.run") as mock_run:
        mock_run.return_value = _completed(stdout="  hello world  \n")
        assert git.read_output("log") == "hello world"
    mock_run.assert_called_once_with(("git", "log"), check=True, text=True, capture_output=True)


def test_repo_root_returns_path() -> None:
    with patch("standard_tooling.lib.git.read_output", return_value="/var/repo"):  # noqa: S108
        result = git.repo_root()
    assert result == Path("/var/repo")


def test_current_branch_returns_name() -> None:
    with patch("standard_tooling.lib.git.read_output", return_value="feature/test"):
        result = git.current_branch()
    assert result == "feature/test"


def test_has_staged_changes_true() -> None:
    with patch("standard_tooling.lib.git.subprocess.run") as mock_run:
        mock_run.return_value = _completed(returncode=1)
        assert git.has_staged_changes() is True


def test_has_staged_changes_false() -> None:
    with patch("standard_tooling.lib.git.subprocess.run") as mock_run:
        mock_run.return_value = _completed(returncode=0)
        assert git.has_staged_changes() is False


def test_ref_exists_true() -> None:
    with patch("standard_tooling.lib.git.subprocess.run") as mock_run:
        mock_run.return_value = _completed(returncode=0)
        assert git.ref_exists("main") is True


def test_ref_exists_false() -> None:
    with patch("standard_tooling.lib.git.subprocess.run") as mock_run:
        mock_run.return_value = _completed(returncode=1)
        assert git.ref_exists("nonexistent") is False


def test_merged_branches_returns_list() -> None:
    with patch("standard_tooling.lib.git.read_output", return_value="feature/a\nfeature/b"):
        result = git.merged_branches("develop")
    assert result == ["feature/a", "feature/b"]


def test_merged_branches_empty() -> None:
    with patch("standard_tooling.lib.git.read_output", return_value=""):
        result = git.merged_branches("develop")
    assert result == []
