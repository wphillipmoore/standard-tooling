"""Tests for standard_tooling.bin.wait_until_green."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from standard_tooling.bin.wait_until_green import main, parse_args

_MOD = "standard_tooling.bin.wait_until_green"


def test_parse_args() -> None:
    args = parse_args(["https://github.com/pr/1"])
    assert args.pr == "https://github.com/pr/1"


def test_main_happy_path() -> None:
    with patch(f"{_MOD}.github.wait_for_checks") as mock_wait:
        result = main(["https://github.com/pr/1"])
    assert result == 0
    mock_wait.assert_called_once_with("https://github.com/pr/1")


def test_main_surfaces_check_failure() -> None:
    err = subprocess.CalledProcessError(returncode=1, cmd=["gh", "pr", "checks"])
    with (
        patch(f"{_MOD}.github.wait_for_checks", side_effect=err),
        pytest.raises(subprocess.CalledProcessError),
    ):
        main(["https://github.com/pr/1"])
