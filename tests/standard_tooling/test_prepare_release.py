"""Tests for standard_tooling.bin.prepare_release."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from standard_tooling.bin.prepare_release import (
    _detect_version_file,
    detect_ecosystem,
    parse_args,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_args() -> None:
    args = parse_args(["--issue", "42"])
    assert args.issue == 42


def test_detect_version_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "VERSION").write_text("2.3.4\n")
    assert _detect_version_file() == "2.3.4"


def test_detect_version_file_invalid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "VERSION").write_text("not-a-version\n")
    with pytest.raises(SystemExit, match="not valid semver"):
        _detect_version_file()


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
