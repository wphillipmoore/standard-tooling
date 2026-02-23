"""Tests for standard_tooling.bin.list_project_repos."""

from __future__ import annotations

from standard_tooling.bin.list_project_repos import parse_args


def test_parse_args() -> None:
    args = parse_args(["--owner", "acme", "--project", "5"])
    assert args.owner == "acme"
    assert args.project == "5"
