"""Tests for standard_tooling.bin.ensure_label."""

from __future__ import annotations

from unittest.mock import patch

from standard_tooling.bin.ensure_label import main, parse_args


def test_parse_args() -> None:
    args = parse_args(["--repo", "owner/repo", "--label", "bug"])
    assert args.repo == "owner/repo"
    assert args.label == "bug"


def test_main_label_exists() -> None:
    with patch("standard_tooling.bin.ensure_label.github.read_output", return_value="bug"):
        result = main(["--repo", "owner/repo", "--label", "bug"])
    assert result == 0


def test_main_label_not_found() -> None:
    with (
        patch("standard_tooling.bin.ensure_label.github.read_output", return_value=""),
        patch("standard_tooling.bin.ensure_label.github.run") as mock_run,
    ):
        result = main(["--repo", "owner/repo", "--label", "bug"])
    assert result == 0
    mock_run.assert_called_once_with("label", "create", "bug", "--repo", "owner/repo")
