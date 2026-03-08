"""Tests for standard_tooling.bin.validate_local_common."""

from __future__ import annotations

from unittest.mock import patch

from standard_tooling.bin.validate_local_common import main


def test_main_sets_env_and_delegates() -> None:
    with (
        patch("standard_tooling.bin.validate_local_common.docker_test.main", return_value=0) as m,
        patch.dict("os.environ", {}, clear=True),
    ):
        result = main()
    assert result == 0
    m.assert_called_once()


def test_main_preserves_custom_image() -> None:
    import os

    captured: dict[str, str] = {}

    def capture_env() -> int:
        captured.update(dict(os.environ))
        return 0

    with (
        patch(
            "standard_tooling.bin.validate_local_common.docker_test.main",
            side_effect=lambda *a, **k: capture_env(),
        ),
        patch.dict("os.environ", {"DOCKER_DEV_IMAGE": "custom:1"}, clear=True),
    ):
        main()
    assert captured["DOCKER_DEV_IMAGE"] == "custom:1"


def test_main_sets_default_image() -> None:
    import os

    captured: dict[str, str] = {}

    def capture_env() -> int:
        captured.update(dict(os.environ))
        return 0

    with (
        patch(
            "standard_tooling.bin.validate_local_common.docker_test.main",
            side_effect=lambda *a, **k: capture_env(),
        ),
        patch.dict("os.environ", {}, clear=True),
    ):
        main()
    assert captured["DOCKER_DEV_IMAGE"] == "dev-python:3.14"


def test_main_sets_cmd() -> None:
    import os

    captured: dict[str, str] = {}

    def capture_env() -> int:
        captured.update(dict(os.environ))
        return 0

    with (
        patch(
            "standard_tooling.bin.validate_local_common.docker_test.main",
            side_effect=lambda *a, **k: capture_env(),
        ),
        patch.dict("os.environ", {}, clear=True),
    ):
        main()
    assert "DOCKER_EXTRA_VOLUMES" not in captured
    assert captured["DOCKER_TEST_CMD"] == "st-validate-local-common-container"


def test_main_propagates_failure() -> None:
    with (
        patch("standard_tooling.bin.validate_local_common.docker_test.main", return_value=1),
        patch.dict("os.environ", {}, clear=True),
    ):
        assert main() == 1
