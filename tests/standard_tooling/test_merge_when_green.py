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


def test_main_happy_path() -> None:
    with (
        patch("standard_tooling.bin.merge_when_green.github.wait_for_checks") as mock_wait,
        patch("standard_tooling.bin.merge_when_green.github.merge") as mock_merge,
    ):
        result = main(["https://github.com/pr/1"])
    assert result == 0
    mock_wait.assert_called_once_with("https://github.com/pr/1")
    mock_merge.assert_called_once_with(
        "https://github.com/pr/1", strategy="merge", delete_branch=True
    )


def test_main_custom_strategy_and_no_delete() -> None:
    with (
        patch("standard_tooling.bin.merge_when_green.github.wait_for_checks"),
        patch("standard_tooling.bin.merge_when_green.github.merge") as mock_merge,
    ):
        result = main(["42", "--strategy", "squash", "--no-delete-branch"])
    assert result == 0
    mock_merge.assert_called_once_with("42", strategy="squash", delete_branch=False)


def test_main_surfaces_check_failure() -> None:
    err = subprocess.CalledProcessError(returncode=1, cmd=["gh", "pr", "checks"])
    with (
        patch(
            "standard_tooling.bin.merge_when_green.github.wait_for_checks",
            side_effect=err,
        ),
        patch("standard_tooling.bin.merge_when_green.github.merge") as mock_merge,
        pytest.raises(subprocess.CalledProcessError),
    ):
        main(["https://github.com/pr/1"])
    mock_merge.assert_not_called()
