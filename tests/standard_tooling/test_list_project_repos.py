"""Tests for standard_tooling.bin.list_project_repos."""

from __future__ import annotations

from unittest.mock import patch

from standard_tooling.bin.list_project_repos import main, parse_args


def test_parse_args() -> None:
    args = parse_args(["--owner", "acme", "--project", "5"])
    assert args.owner == "acme"
    assert args.project == "5"


def test_main_lists_repos() -> None:
    with patch(
        "standard_tooling.bin.list_project_repos.github.read_output",
        return_value="acme/repo-b\nacme/repo-a\nacme/repo-a\n",
    ):
        result = main(["--owner", "acme", "--project", "5"])
    assert result == 0


def test_main_with_empty_lines() -> None:
    with patch(
        "standard_tooling.bin.list_project_repos.github.read_output",
        return_value="acme/repo-a\n\nacme/repo-b\n",
    ):
        result = main(["--owner", "acme", "--project", "5"])
    assert result == 0


def test_main_no_repos() -> None:
    with patch(
        "standard_tooling.bin.list_project_repos.github.read_output",
        return_value="",
    ):
        result = main(["--owner", "acme", "--project", "5"])
    assert result == 0
