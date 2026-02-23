"""Tests for standard_tooling.bin.prepare_release."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from standard_tooling.bin.prepare_release import (
    _detect_go,
    _detect_maven,
    _detect_python,
    _detect_version_file,
    _ensure_clean_tree,
    _ensure_develop_up_to_date,
    _ensure_on_develop,
    _ensure_tool,
    detect_ecosystem,
    main,
    parse_args,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_args() -> None:
    args = parse_args(["--issue", "42"])
    assert args.issue == 42


# -- ecosystem detection tests ---


def test_detect_python(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "3.1.0"\n')
    assert _detect_python() == "3.1.0"


def test_detect_python_no_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert _detect_python() is None


def test_detect_python_no_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'foo'\n")
    assert _detect_python() is None


def test_detect_maven(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pom.xml").write_text(
        "<project><artifactId>foo</artifactId><version>2.0.0</version></project>"
    )
    assert _detect_maven() == "2.0.0"


def test_detect_maven_no_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert _detect_maven() is None


def test_detect_maven_no_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pom.xml").write_text("<project><groupId>g</groupId></project>")
    assert _detect_maven() is None


def test_detect_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example\n")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "version.go").write_text('package pkg\nconst Version = "1.5.0"\n')
    assert _detect_go() == "1.5.0"


def test_detect_go_no_mod(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert _detect_go() is None


def test_detect_go_no_version_in_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example\n")
    (tmp_path / "version.go").write_text("package main\n")
    assert _detect_go() is None


def test_detect_version_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "VERSION").write_text("2.3.4\n")
    assert _detect_version_file() == "2.3.4"


def test_detect_version_file_no_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert _detect_version_file() is None


def test_detect_version_file_invalid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "VERSION").write_text("not-a-version\n")
    with pytest.raises(SystemExit, match="not valid semver"):
        _detect_version_file()


def test_detect_ecosystem_python(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "1.0.0"\n')
    name, version = detect_ecosystem()
    assert name == "python"
    assert version == "1.0.0"


def test_detect_ecosystem_version_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "VERSION").write_text("1.0.0\n")
    name, version = detect_ecosystem()
    assert name == "version-file"
    assert version == "1.0.0"


def test_detect_ecosystem_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="Could not detect ecosystem"):
        detect_ecosystem()


# -- precondition check tests ---


def test_ensure_on_develop_ok() -> None:
    with patch("standard_tooling.bin.prepare_release.git.current_branch", return_value="develop"):
        _ensure_on_develop()


def test_ensure_on_develop_wrong_branch() -> None:
    with (
        patch(
            "standard_tooling.bin.prepare_release.git.current_branch",
            return_value="feature/x",
        ),
        pytest.raises(SystemExit, match="Must be on develop"),
    ):
        _ensure_on_develop()


def test_ensure_clean_tree_ok() -> None:
    with patch("standard_tooling.bin.prepare_release.git.read_output", return_value=""):
        _ensure_clean_tree()


def test_ensure_clean_tree_dirty() -> None:
    with (
        patch("standard_tooling.bin.prepare_release.git.read_output", return_value="M file.py"),
        pytest.raises(SystemExit, match="Working tree is not clean"),
    ):
        _ensure_clean_tree()


def test_ensure_develop_up_to_date_ok() -> None:
    with (
        patch("standard_tooling.bin.prepare_release.git.run"),
        patch("standard_tooling.bin.prepare_release.git.read_output", return_value="abc123"),
    ):
        _ensure_develop_up_to_date()


def test_ensure_develop_up_to_date_diverged() -> None:
    call_count = 0

    def mock_read_output(*args: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "abc123"
        return "def456"

    with (
        patch("standard_tooling.bin.prepare_release.git.run"),
        patch(
            "standard_tooling.bin.prepare_release.git.read_output",
            side_effect=mock_read_output,
        ),
        pytest.raises(SystemExit, match="does not match"),
    ):
        _ensure_develop_up_to_date()


def test_ensure_tool_found() -> None:
    with patch("standard_tooling.bin.prepare_release.shutil.which", return_value="/usr/bin/gh"):
        _ensure_tool("gh")


def test_ensure_tool_not_found() -> None:
    with (
        patch("standard_tooling.bin.prepare_release.shutil.which", return_value=None),
        pytest.raises(SystemExit, match="not found on PATH"),
    ):
        _ensure_tool("missing-tool")


# -- main flow tests ---


def _smart_read_output(status_return: str = "M CHANGELOG.md") -> object:
    """Return a mock for git.read_output that handles all call patterns in main()."""

    def _mock(*args: str) -> str:
        if args[0] == "status":
            return status_return
        if args[0] == "rev-parse":
            return "abc123"
        return ""

    return _mock


def test_main_full_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "1.0.0"\n')

    # _ensure_clean_tree reads status --porcelain, needs "" first time, then
    # _generate_changelog reads it again, needs non-empty second time
    status_calls = 0

    def mock_read_output(*args: str) -> str:
        nonlocal status_calls
        if args[0] == "status":
            status_calls += 1
            if status_calls == 1:
                return ""  # _ensure_clean_tree: clean
            return "M CHANGELOG.md"  # _generate_changelog: has changes
        if args[0] == "rev-parse":
            return "abc123"
        return ""

    def mock_subprocess_run(
        cmd: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if "git-cliff" in cmd:
            (tmp_path / "CHANGELOG.md").write_text("# Changelog\n")
        return subprocess.CompletedProcess(args=list(cmd), returncode=0, stdout="", stderr="")

    with (
        patch(
            "standard_tooling.bin.prepare_release.git.current_branch",
            return_value="develop",
        ),
        patch("standard_tooling.bin.prepare_release.git.run"),
        patch(
            "standard_tooling.bin.prepare_release.git.read_output",
            side_effect=mock_read_output,
        ),
        patch("standard_tooling.bin.prepare_release.git.ref_exists", return_value=False),
        patch(
            "standard_tooling.bin.prepare_release.shutil.which",
            return_value="/usr/bin/tool",
        ),
        patch(
            "standard_tooling.bin.prepare_release.subprocess.run",
            side_effect=mock_subprocess_run,
        ),
        patch(
            "standard_tooling.bin.prepare_release.github.create_pr",
            return_value="https://github.com/pr/1",
        ),
        patch("standard_tooling.bin.prepare_release.github.auto_merge"),
    ):
        result = main(["--issue", "42"])
    assert result == 0


def test_main_release_branch_already_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "1.0.0"\n')

    def mock_read_output(*args: str) -> str:
        if args[0] == "status":
            return ""
        if args[0] == "rev-parse":
            return "abc123"
        return ""

    with (
        patch(
            "standard_tooling.bin.prepare_release.git.current_branch",
            return_value="develop",
        ),
        patch("standard_tooling.bin.prepare_release.git.run"),
        patch(
            "standard_tooling.bin.prepare_release.git.read_output",
            side_effect=mock_read_output,
        ),
        patch("standard_tooling.bin.prepare_release.git.ref_exists", return_value=True),
        patch(
            "standard_tooling.bin.prepare_release.shutil.which",
            return_value="/usr/bin/tool",
        ),
        pytest.raises(SystemExit, match="already exists"),
    ):
        main(["--issue", "42"])


def test_main_no_publishable_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "1.0.0"\n')

    def mock_read_output(*args: str) -> str:
        if args[0] == "status":
            return ""  # both times: clean tree + no changes after changelog
        if args[0] == "rev-parse":
            return "abc123"
        return ""

    def mock_subprocess_run(
        cmd: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if "git-cliff" in cmd:
            (tmp_path / "CHANGELOG.md").write_text("# Changelog\n")
        return subprocess.CompletedProcess(args=list(cmd), returncode=0, stdout="", stderr="")

    with (
        patch(
            "standard_tooling.bin.prepare_release.git.current_branch",
            return_value="develop",
        ),
        patch("standard_tooling.bin.prepare_release.git.run"),
        patch(
            "standard_tooling.bin.prepare_release.git.read_output",
            side_effect=mock_read_output,
        ),
        patch("standard_tooling.bin.prepare_release.git.ref_exists", return_value=False),
        patch(
            "standard_tooling.bin.prepare_release.shutil.which",
            return_value="/usr/bin/tool",
        ),
        patch(
            "standard_tooling.bin.prepare_release.subprocess.run",
            side_effect=mock_subprocess_run,
        ),
        pytest.raises(SystemExit, match="No publishable changes"),
    ):
        main(["--issue", "42"])


def test_main_changelog_lint_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('version = "1.0.0"\n')

    def mock_read_output(*args: str) -> str:
        if args[0] == "status":
            return ""
        if args[0] == "rev-parse":
            return "abc123"
        return ""

    def mock_subprocess_run(
        cmd: tuple[str, ...], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if "git-cliff" in cmd:
            (tmp_path / "CHANGELOG.md").write_text("# Changelog\n")
            return subprocess.CompletedProcess(args=list(cmd), returncode=0, stdout="", stderr="")
        if "markdownlint" in cmd:
            return subprocess.CompletedProcess(
                args=list(cmd), returncode=1, stdout="lint error", stderr="detail"
            )
        return subprocess.CompletedProcess(args=list(cmd), returncode=0, stdout="", stderr="")

    with (
        patch(
            "standard_tooling.bin.prepare_release.git.current_branch",
            return_value="develop",
        ),
        patch("standard_tooling.bin.prepare_release.git.run"),
        patch(
            "standard_tooling.bin.prepare_release.git.read_output",
            side_effect=mock_read_output,
        ),
        patch("standard_tooling.bin.prepare_release.git.ref_exists", return_value=False),
        patch(
            "standard_tooling.bin.prepare_release.shutil.which",
            return_value="/usr/bin/tool",
        ),
        patch(
            "standard_tooling.bin.prepare_release.subprocess.run",
            side_effect=mock_subprocess_run,
        ),
        pytest.raises(SystemExit, match="failed markdownlint"),
    ):
        main(["--issue", "42"])
