"""Tests for standard_tooling.bin.set_project_field."""

from __future__ import annotations

from unittest.mock import patch

from standard_tooling.bin.set_project_field import main, parse_args


def test_parse_args() -> None:
    args = parse_args(
        [
            "--owner",
            "acme",
            "--project",
            "5",
            "--item",
            "PVTI_123",
            "--field",
            "Status",
            "--value",
            "Done",
        ]
    )
    assert args.owner == "acme"
    assert args.project == "5"
    assert args.item == "PVTI_123"
    assert args.field == "Status"
    assert args.value == "Done"


def test_main_success() -> None:
    with (
        patch(
            "standard_tooling.bin.set_project_field.github.read_output",
            side_effect=["PVT_abc123", "FIELD_1 OPT_2"],
        ),
        patch("standard_tooling.bin.set_project_field.github.run") as mock_run,
    ):
        result = main(
            [
                "--owner",
                "acme",
                "--project",
                "5",
                "--item",
                "PVTI_123",
                "--field",
                "Status",
                "--value",
                "Done",
            ]
        )
    assert result == 0
    mock_run.assert_called_once_with(
        "project",
        "item-edit",
        "--project-id",
        "PVT_abc123",
        "--id",
        "PVTI_123",
        "--field-id",
        "FIELD_1",
        "--single-select-option-id",
        "OPT_2",
    )


def test_main_field_not_found() -> None:
    with patch(
        "standard_tooling.bin.set_project_field.github.read_output",
        side_effect=["PVT_abc123", ""],
    ):
        result = main(
            [
                "--owner",
                "acme",
                "--project",
                "5",
                "--item",
                "PVTI_123",
                "--field",
                "Missing",
                "--value",
                "Done",
            ]
        )
    assert result == 1


def test_main_option_not_found() -> None:
    with patch(
        "standard_tooling.bin.set_project_field.github.read_output",
        side_effect=["PVT_abc123", "FIELD_1"],
    ):
        result = main(
            [
                "--owner",
                "acme",
                "--project",
                "5",
                "--item",
                "PVTI_123",
                "--field",
                "Status",
                "--value",
                "Missing",
            ]
        )
    assert result == 1
