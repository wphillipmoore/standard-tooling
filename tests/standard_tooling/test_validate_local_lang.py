"""Tests for standard_tooling.bin.validate_local_lang."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.validate_local_lang import _detect_language, main

if TYPE_CHECKING:
    from pathlib import Path


# -- _detect_language ---------------------------------------------------------


def test_detect_from_argv() -> None:
    assert _detect_language(["--language", "python"]) == "python"


def test_detect_from_entry_point() -> None:
    with patch("standard_tooling.bin.validate_local_lang.sys.argv", ["st-validate-local-rust"]):
        assert _detect_language(None) == "rust"


def test_detect_from_entry_point_go() -> None:
    with patch("standard_tooling.bin.validate_local_lang.sys.argv", ["st-validate-local-go"]):
        assert _detect_language(None) == "go"


def test_detect_from_entry_point_java() -> None:
    with patch("standard_tooling.bin.validate_local_lang.sys.argv", ["st-validate-local-java"]):
        assert _detect_language(None) == "java"


def test_detect_from_entry_point_python() -> None:
    with patch("standard_tooling.bin.validate_local_lang.sys.argv", ["st-validate-local-python"]):
        assert _detect_language(None) == "python"


def test_detect_unknown_entry_point() -> None:
    with patch("standard_tooling.bin.validate_local_lang.sys.argv", ["some-other-script"]):
        assert _detect_language(None) == ""


def test_detect_argv_overrides_entry_point() -> None:
    with patch("standard_tooling.bin.validate_local_lang.sys.argv", ["st-validate-local-go"]):
        assert _detect_language(["--language", "rust"]) == "rust"


# -- main --------------------------------------------------------------------


def test_main_no_language() -> None:
    with patch("standard_tooling.bin.validate_local_lang.sys.argv", ["unknown"]):
        assert main([]) == 1


def test_main_all_scripts_pass(tmp_path: Path) -> None:
    dev = tmp_path / "scripts" / "dev"
    dev.mkdir(parents=True)
    for name in ("lint.sh", "typecheck.sh", "test.sh", "audit.sh"):
        script = dev / name
        script.write_text("#!/bin/bash\nexit 0\n")
        script.chmod(0o755)

    with (
        patch(
            "standard_tooling.bin.validate_local_lang.git.repo_root",
            return_value=tmp_path,
        ),
        patch(
            "standard_tooling.bin.validate_local_lang.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ),
    ):
        assert main(["--language", "python"]) == 0


def test_main_script_fails(tmp_path: Path) -> None:
    dev = tmp_path / "scripts" / "dev"
    dev.mkdir(parents=True)
    lint = dev / "lint.sh"
    lint.write_text("#!/bin/bash\nexit 1\n")
    lint.chmod(0o755)

    with (
        patch(
            "standard_tooling.bin.validate_local_lang.git.repo_root",
            return_value=tmp_path,
        ),
        patch(
            "standard_tooling.bin.validate_local_lang.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=1),
        ),
    ):
        assert main(["--language", "python"]) == 1


def test_main_no_scripts(tmp_path: Path) -> None:
    with patch(
        "standard_tooling.bin.validate_local_lang.git.repo_root",
        return_value=tmp_path,
    ):
        assert main(["--language", "go"]) == 0


def test_main_skips_non_executable(tmp_path: Path) -> None:
    dev = tmp_path / "scripts" / "dev"
    dev.mkdir(parents=True)
    lint = dev / "lint.sh"
    lint.write_text("#!/bin/bash\nexit 0\n")
    lint.chmod(0o644)

    with patch(
        "standard_tooling.bin.validate_local_lang.git.repo_root",
        return_value=tmp_path,
    ):
        assert main(["--language", "python"]) == 0
