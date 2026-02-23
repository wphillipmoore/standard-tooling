"""Tests for standard_tooling.bin.finalize_repo."""

from __future__ import annotations

from standard_tooling.bin.finalize_repo import parse_args


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.target_branch == "develop"
    assert args.dry_run is False


def test_parse_args_custom() -> None:
    args = parse_args(["--target-branch", "main", "--dry-run"])
    assert args.target_branch == "main"
    assert args.dry_run is True
