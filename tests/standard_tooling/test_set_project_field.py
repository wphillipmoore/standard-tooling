"""Tests for standard_tooling.bin.set_project_field."""

from __future__ import annotations

from standard_tooling.bin.set_project_field import parse_args


def test_parse_args() -> None:
    args = parse_args([
        "--owner", "acme", "--project", "5",
        "--item", "PVTI_123", "--field", "Status", "--value", "Done",
    ])
    assert args.owner == "acme"
    assert args.project == "5"
    assert args.item == "PVTI_123"
    assert args.field == "Status"
    assert args.value == "Done"
