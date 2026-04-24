"""Tests for standard_tooling.bin.validate_local_common."""

from __future__ import annotations

from unittest.mock import patch

from standard_tooling.bin.validate_local_common import main


def test_main_delegates_to_container_impl() -> None:
    with patch(
        "standard_tooling.bin.validate_local_common."
        "validate_local_common_container.main",
        return_value=0,
    ) as m:
        result = main()
    assert result == 0
    m.assert_called_once()


def test_main_propagates_failure() -> None:
    with patch(
        "standard_tooling.bin.validate_local_common."
        "validate_local_common_container.main",
        return_value=1,
    ):
        assert main() == 1
