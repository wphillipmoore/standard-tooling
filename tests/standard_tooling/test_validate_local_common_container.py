"""Tests for standard_tooling.bin.validate_local_common_container."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.validate_local_common_container import (
    _find_shell_files,
    _find_yaml_files,
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


# -- _find_yaml_files --------------------------------------------------------


def test_find_yaml_files_none(tmp_path: Path) -> None:
    assert _find_yaml_files(tmp_path) == []


def test_find_yaml_files_repo_root(tmp_path: Path) -> None:
    (tmp_path / ".markdownlint.yaml").write_text("default: true\n")
    (tmp_path / ".yamllint").write_text("extends: default\n")  # no .yml/.yaml suffix
    result = _find_yaml_files(tmp_path)
    assert len(result) == 1
    assert result[0].endswith(".markdownlint.yaml")


def test_find_yaml_files_github_workflows(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n")
    (workflows / "release.yaml").write_text("name: Release\n")
    result = _find_yaml_files(tmp_path)
    assert len(result) == 2


def test_find_yaml_files_github_issue_templates(tmp_path: Path) -> None:
    templates = tmp_path / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir(parents=True)
    (templates / "issue.yml").write_text("name: Issue\n")
    result = _find_yaml_files(tmp_path)
    assert any(p.endswith("issue.yml") for p in result)


def test_find_yaml_files_mkdocs(tmp_path: Path) -> None:
    docs_site = tmp_path / "docs" / "site"
    docs_site.mkdir(parents=True)
    (docs_site / "mkdocs.yml").write_text("site_name: docs\n")
    result = _find_yaml_files(tmp_path)
    assert len(result) == 1
    assert result[0].endswith("mkdocs.yml")


def test_find_yaml_files_skips_worktrees_and_venv(tmp_path: Path) -> None:
    # Files in skipped subtrees must not appear, even though they have a
    # YAML extension.
    for skip in (".worktrees", ".venv", ".venv-host", "node_modules"):
        nested = tmp_path / skip / ".github" / "workflows"
        nested.mkdir(parents=True)
        (nested / "ci.yml").write_text("name: CI\n")
    # And a real workflow at the proper path:
    real = tmp_path / ".github" / "workflows"
    real.mkdir(parents=True)
    (real / "ci.yml").write_text("name: CI\n")
    result = _find_yaml_files(tmp_path)
    assert len(result) == 1
    assert ".worktrees" not in result[0]
    assert ".venv" not in result[0]


def test_find_yaml_files_sorted_and_deduped(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "b.yml").write_text("name: b\n")
    (workflows / "a.yml").write_text("name: a\n")
    result = _find_yaml_files(tmp_path)
    assert result == sorted(result)
    assert len(result) == len(set(result))


# -- main: yamllint path -----------------------------------------------------


def test_main_yamllint_runs(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n")

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
    # Only yamllint runs (no shell files in this fixture).
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "yamllint"


def test_main_yamllint_fails(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n")

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
