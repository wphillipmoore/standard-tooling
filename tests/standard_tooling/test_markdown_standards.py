"""Tests for standard_tooling.bin.markdown_standards."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.markdown_standards import _find_files, main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


# -- _find_files -------------------------------------------------------------


def test_find_files_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert _find_files() == []


def test_find_files_site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    site = tmp_path / "docs" / "site"
    site.mkdir(parents=True)
    (site / "index.md").write_text("# Hello\n")
    result = _find_files()
    assert len(result) == 1
    assert "index.md" in result[0]


def test_find_files_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    result = _find_files()
    assert result == ["README.md"]


# -- main --------------------------------------------------------------------


def test_main_no_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main([]) == 0


def test_main_markdownlint_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    with patch("standard_tooling.bin.markdown_standards.shutil.which", return_value=None):
        assert main([]) == 2


def test_main_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    with (
        patch("standard_tooling.bin.markdown_standards.shutil.which", return_value="/usr/bin/ml"),
        patch(
            "standard_tooling.bin.markdown_standards.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ),
    ):
        assert main([]) == 0


def test_main_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    with (
        patch("standard_tooling.bin.markdown_standards.shutil.which", return_value="/usr/bin/ml"),
        patch(
            "standard_tooling.bin.markdown_standards.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=1),
        ),
    ):
        assert main([]) == 1


def test_main_with_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    (tmp_path / ".markdownlint.yaml").write_text("default: true\n")
    captured_cmd: list[str] = []

    def capture_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        captured_cmd.extend(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    with (
        patch("standard_tooling.bin.markdown_standards.shutil.which", return_value="/usr/bin/ml"),
        patch("standard_tooling.bin.markdown_standards.subprocess.run", side_effect=capture_run),
    ):
        main([])
    assert "--config" in captured_cmd
    assert ".markdownlint.yaml" in captured_cmd
