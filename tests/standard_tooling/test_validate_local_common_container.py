"""Tests for standard_tooling.bin.validate_local_common_container."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.validate_local_common_container import (
    _find_shell_files,
    main,
)

if TYPE_CHECKING:
    from pathlib import Path


# -- _find_shell_files --------------------------------------------------------


def test_find_shell_files_none(tmp_path: Path) -> None:
    assert _find_shell_files(tmp_path) == []


def test_find_shell_files_discovers_sh(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts" / "dev"
    scripts.mkdir(parents=True)
    (scripts / "lint.sh").write_text("#!/bin/bash\n")
    result = _find_shell_files(tmp_path)
    assert len(result) == 1
    assert result[0].endswith("lint.sh")


def test_find_shell_files_discovers_bin(tmp_path: Path) -> None:
    scripts_bin = tmp_path / "scripts" / "bin"
    scripts_bin.mkdir(parents=True)
    (scripts_bin / "my-script").write_text("#!/bin/bash\n")
    result = _find_shell_files(tmp_path)
    assert len(result) == 1
    assert "my-script" in result[0]


def test_find_shell_files_discovers_git_hooks(tmp_path: Path) -> None:
    hooks = tmp_path / "scripts" / "lib" / "git-hooks"
    hooks.mkdir(parents=True)
    (hooks / "pre-commit").write_text("#!/bin/bash\n")
    result = _find_shell_files(tmp_path)
    assert len(result) == 1
    assert "pre-commit" in result[0]


def test_find_shell_files_skips_non_matching(tmp_path: Path) -> None:
    lib = tmp_path / "scripts" / "lib"
    lib.mkdir(parents=True)
    (lib / "README.md").write_text("# Not a shell file\n")
    result = _find_shell_files(tmp_path)
    assert result == []


def test_find_shell_files_sorted(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts" / "dev"
    scripts.mkdir(parents=True)
    (scripts / "b.sh").write_text("#!/bin/bash\n")
    (scripts / "a.sh").write_text("#!/bin/bash\n")
    result = _find_shell_files(tmp_path)
    assert result[0] < result[1]


# -- main --------------------------------------------------------------------


def test_main_all_pass(tmp_path: Path) -> None:
    with (
        patch(
            "standard_tooling.bin.validate_local_common_container.git.repo_root",
            return_value=tmp_path,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.repo_profile_cli.main",
            return_value=0,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.markdown_standards.main",
            return_value=0,
        ),
    ):
        assert main() == 0


def test_main_repo_profile_fails(tmp_path: Path) -> None:
    with (
        patch(
            "standard_tooling.bin.validate_local_common_container.git.repo_root",
            return_value=tmp_path,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.repo_profile_cli.main",
            return_value=1,
        ),
    ):
        assert main() == 1


def test_main_markdown_fails(tmp_path: Path) -> None:
    with (
        patch(
            "standard_tooling.bin.validate_local_common_container.git.repo_root",
            return_value=tmp_path,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.repo_profile_cli.main",
            return_value=0,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.markdown_standards.main",
            return_value=1,
        ),
    ):
        assert main() == 1


def test_main_shellcheck_runs(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts" / "dev"
    scripts.mkdir(parents=True)
    (scripts / "lint.sh").write_text("#!/bin/bash\n")

    with (
        patch(
            "standard_tooling.bin.validate_local_common_container.git.repo_root",
            return_value=tmp_path,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.repo_profile_cli.main",
            return_value=0,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.markdown_standards.main",
            return_value=0,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ) as mock_run,
    ):
        assert main() == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "shellcheck"


def test_main_shellcheck_fails(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts" / "dev"
    scripts.mkdir(parents=True)
    (scripts / "lint.sh").write_text("#!/bin/bash\n")

    with (
        patch(
            "standard_tooling.bin.validate_local_common_container.git.repo_root",
            return_value=tmp_path,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.repo_profile_cli.main",
            return_value=0,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.markdown_standards.main",
            return_value=0,
        ),
        patch(
            "standard_tooling.bin.validate_local_common_container.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=1),
        ),
    ):
        assert main() == 1
