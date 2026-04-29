"""Tests for standard_tooling.bin.merge_when_green."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from standard_tooling.bin.merge_when_green import main, parse_args


def test_parse_args_defaults() -> None:
    args = parse_args(["https://github.com/pr/1"])
    assert args.pr == "https://github.com/pr/1"
    assert args.strategy == "merge"
    assert args.delete_branch is True


def test_parse_args_strategy() -> None:
    args = parse_args(["42", "--strategy", "squash"])
    assert args.strategy == "squash"


def test_parse_args_no_delete_branch() -> None:
    args = parse_args(["42", "--no-delete-branch"])
    assert args.delete_branch is False


def test_parse_args_rejects_unknown_strategy() -> None:
    with pytest.raises(SystemExit):
        parse_args(["42", "--strategy", "ff-only"])


_MOD = "standard_tooling.bin.merge_when_green"


def _mock_branch(branch: str = "release/1.0.0"):
    """Return a patch that mocks github.read_output to return a branch name."""
    return patch(f"{_MOD}.github.read_output", return_value=branch)


def test_main_happy_path() -> None:
    with (
        _mock_branch("release/1.0.0"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=True),
        patch(f"{_MOD}.github.wait_for_checks") as mock_wait,
        patch(f"{_MOD}.github.merge") as mock_merge,
    ):
        result = main(["https://github.com/pr/1"])
    assert result == 0
    mock_wait.assert_called_once_with("https://github.com/pr/1")
    mock_merge.assert_called_once_with(
        "https://github.com/pr/1", strategy="merge", delete_branch=True
    )


def test_main_custom_strategy_and_no_delete() -> None:
    with (
        _mock_branch("release/1.0.0"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=True),
        patch(f"{_MOD}.github.wait_for_checks"),
        patch(f"{_MOD}.github.merge") as mock_merge,
    ):
        result = main(["42", "--strategy", "squash", "--no-delete-branch"])
    assert result == 0
    mock_merge.assert_called_once_with("42", strategy="squash", delete_branch=False)


def test_main_skips_delete_branch_in_worktree(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        _mock_branch("release/1.0.0"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=False),
        patch(f"{_MOD}.github.wait_for_checks"),
        patch(f"{_MOD}.github.merge") as mock_merge,
    ):
        result = main(["https://github.com/pr/1"])
    assert result == 0
    mock_merge.assert_called_once_with(
        "https://github.com/pr/1", strategy="merge", delete_branch=False
    )
    assert "skipping --delete-branch" in capsys.readouterr().out


def test_main_worktree_respects_explicit_no_delete() -> None:
    with (
        _mock_branch("release/1.0.0"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=False),
        patch(f"{_MOD}.github.wait_for_checks"),
        patch(f"{_MOD}.github.merge") as mock_merge,
    ):
        result = main(["42", "--no-delete-branch"])
    assert result == 0
    mock_merge.assert_called_once_with("42", strategy="merge", delete_branch=False)


def test_main_surfaces_check_failure() -> None:
    err = subprocess.CalledProcessError(returncode=1, cmd=["gh", "pr", "checks"])
    with (
        _mock_branch("release/1.0.0"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=True),
        patch(
            f"{_MOD}.github.wait_for_checks",
            side_effect=err,
        ),
        patch(f"{_MOD}.github.merge") as mock_merge,
        pytest.raises(subprocess.CalledProcessError),
    ):
        main(["https://github.com/pr/1"])
    mock_merge.assert_not_called()


def test_release_branch_allowed() -> None:
    with (
        _mock_branch("release/1.4.9"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=True),
        patch(f"{_MOD}.github.wait_for_checks"),
        patch(f"{_MOD}.github.merge") as mock_merge,
    ):
        result = main(["https://github.com/pr/1"])
    assert result == 0
    mock_merge.assert_called_once()


def test_bump_branch_allowed() -> None:
    with (
        _mock_branch("chore/bump-version-1.4.10"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=True),
        patch(f"{_MOD}.github.wait_for_checks"),
        patch(f"{_MOD}.github.merge") as mock_merge,
    ):
        result = main(["https://github.com/pr/1"])
    assert result == 0
    mock_merge.assert_called_once()


def test_feature_branch_blocked(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        _mock_branch("feature/42-foo"),
        patch(f"{_MOD}.git.is_main_worktree", return_value=True),
        patch(f"{_MOD}.github.wait_for_checks") as mock_wait,
        patch(f"{_MOD}.github.merge") as mock_merge,
    ):
        result = main(["https://github.com/pr/1"])
    assert result == 1
    mock_wait.assert_not_called()
    mock_merge.assert_not_called()
    assert "only for release-workflow PRs" in capsys.readouterr().err
