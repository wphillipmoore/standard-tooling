"""Tests for standard_tooling.bin.validate_local."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from standard_tooling.bin.validate_local import _find_validator, _run_validator, main


def test_find_validator_on_path() -> None:
    with patch("standard_tooling.bin.validate_local.shutil.which", return_value="/usr/bin/v"):
        result = _find_validator("v", Path("/scripts/bin"))
    assert result == "/usr/bin/v"


def test_find_validator_local_fallback(tmp_path: Path) -> None:
    scripts_bin = tmp_path / "scripts" / "bin"
    scripts_bin.mkdir(parents=True)
    validator = scripts_bin / "validate-local-common"
    validator.write_text("#!/bin/bash\nexit 0\n")
    validator.chmod(0o755)
    with patch("standard_tooling.bin.validate_local.shutil.which", return_value=None):
        result = _find_validator("validate-local-common", scripts_bin)
    assert result == str(validator)


def test_find_validator_not_found(tmp_path: Path) -> None:
    with patch("standard_tooling.bin.validate_local.shutil.which", return_value=None):
        result = _find_validator("nonexistent", tmp_path)
    assert result is None


def test_find_validator_local_not_executable(tmp_path: Path) -> None:
    scripts_bin = tmp_path / "scripts" / "bin"
    scripts_bin.mkdir(parents=True)
    validator = scripts_bin / "validate-local-common"
    validator.write_text("#!/bin/bash\nexit 0\n")
    validator.chmod(0o644)
    with patch("standard_tooling.bin.validate_local.shutil.which", return_value=None):
        result = _find_validator("validate-local-common", scripts_bin)
    assert result is None


def test_run_validator_success(tmp_path: Path) -> None:
    with (
        patch(
            "standard_tooling.bin.validate_local._find_validator",
            return_value="/usr/bin/v",
        ),
        patch(
            "standard_tooling.bin.validate_local.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ),
    ):
        assert _run_validator("v", tmp_path) is True


def test_run_validator_failure(tmp_path: Path) -> None:
    with (
        patch(
            "standard_tooling.bin.validate_local._find_validator",
            return_value="/usr/bin/v",
        ),
        patch(
            "standard_tooling.bin.validate_local.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=1),
        ),
    ):
        assert _run_validator("v", tmp_path) is False


def test_run_validator_not_found(tmp_path: Path) -> None:
    with patch("standard_tooling.bin.validate_local._find_validator", return_value=None):
        assert _run_validator("missing", tmp_path) is True


def _make_profile(tmp_path: Path, language: str) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "repository-standards.md").write_text(
        f"## Repository profile\n\n- primary_language: {language}\n"
    )


def test_main_all_pass(tmp_path: Path) -> None:
    _make_profile(tmp_path, "python")
    scripts_bin = tmp_path / "scripts" / "bin"
    scripts_bin.mkdir(parents=True)
    with (
        patch("standard_tooling.bin.validate_local.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.validate_local._find_validator", return_value=None),
    ):
        result = main([])
    assert result == 0


def test_main_common_fails(tmp_path: Path) -> None:
    _make_profile(tmp_path, "python")
    call_count = 0

    def mock_run_validator(name: str, scripts_bin: Path) -> bool:
        nonlocal call_count
        call_count += 1
        return name != "validate-local-common"

    with (
        patch("standard_tooling.bin.validate_local.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.validate_local._run_validator",
            side_effect=mock_run_validator,
        ),
    ):
        result = main([])
    assert result == 1


def test_main_language_validator_fails(tmp_path: Path) -> None:
    _make_profile(tmp_path, "python")

    def mock_run_validator(name: str, scripts_bin: Path) -> bool:
        return name != "validate-local-python"

    with (
        patch("standard_tooling.bin.validate_local.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.validate_local._run_validator",
            side_effect=mock_run_validator,
        ),
    ):
        result = main([])
    assert result == 1


def test_main_no_profile(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.validate_local.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.validate_local._find_validator", return_value=None),
    ):
        result = main([])
    assert result == 0


def test_main_language_none(tmp_path: Path) -> None:
    _make_profile(tmp_path, "none")
    with (
        patch("standard_tooling.bin.validate_local.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.validate_local._run_validator", return_value=True),
        patch("standard_tooling.bin.validate_local._find_validator", return_value=None),
    ):
        result = main([])
    assert result == 0


def test_main_custom_validator_exists(tmp_path: Path) -> None:
    _make_profile(tmp_path, "python")
    call_count = 0

    def mock_find_validator(name: str, scripts_bin: Path) -> str | None:
        if name == "validate-local-custom":
            return "/path/to/custom"
        return None

    def mock_run_validator(name: str, scripts_bin: Path) -> bool:
        nonlocal call_count
        call_count += 1
        return True

    with (
        patch("standard_tooling.bin.validate_local.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.validate_local._run_validator",
            side_effect=mock_run_validator,
        ),
        patch(
            "standard_tooling.bin.validate_local._find_validator",
            side_effect=mock_find_validator,
        ),
    ):
        result = main([])
    assert result == 0
    assert call_count == 3


def test_main_custom_validator_fails(tmp_path: Path) -> None:
    def mock_find_validator(name: str, scripts_bin: Path) -> str | None:
        if name == "validate-local-custom":
            return "/path/to/custom"
        return None

    def mock_run_validator(name: str, scripts_bin: Path) -> bool:
        return name != "validate-local-custom"

    _make_profile(tmp_path, "python")
    with (
        patch("standard_tooling.bin.validate_local.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.validate_local._run_validator",
            side_effect=mock_run_validator,
        ),
        patch(
            "standard_tooling.bin.validate_local._find_validator",
            side_effect=mock_find_validator,
        ),
    ):
        result = main([])
    assert result == 1
