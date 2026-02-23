"""Tests for standard_tooling.bin.ensure_label."""

from __future__ import annotations

from standard_tooling.bin.ensure_label import parse_args


def test_parse_args() -> None:
    args = parse_args(["--repo", "owner/repo", "--label", "bug"])
    assert args.repo == "owner/repo"
    assert args.label == "bug"
