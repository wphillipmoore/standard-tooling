"""Tests for standard_tooling.bin.docker_cache CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from standard_tooling.bin.docker_cache import main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


# -- no subcommand ------------------------------------------------------------


def test_no_subcommand() -> None:
    assert main([]) == 1


# -- build subcommand ---------------------------------------------------------


def test_build_calls_ensure(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.docker_cache.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_cache.assert_docker_available"),
        patch("standard_tooling.bin.docker_cache.ensure_cached_image", return_value="img:cached"),
    ):
        assert main(["build"]) == 0


# -- status subcommand --------------------------------------------------------


def test_status_no_cache(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("standard_tooling.bin.docker_cache.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_cache.git.current_branch", return_value="feature/42"),
        patch("standard_tooling.bin.docker_cache.find_cached_image", return_value=None),
    ):
        assert main(["status"]) == 0
    assert "No cached image" in capsys.readouterr().out


def test_status_with_cache(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cached = ("img:1.26--feature-42--abcd1234", "abcd1234")
    with (
        patch("standard_tooling.bin.docker_cache.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_cache.git.current_branch", return_value="feature/42"),
        patch("standard_tooling.bin.docker_cache.find_cached_image", return_value=cached),
    ):
        assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "abcd1234" in out


# -- clean subcommand ---------------------------------------------------------


def test_clean_no_cache(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("standard_tooling.bin.docker_cache.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_cache.git.current_branch", return_value="feature/42"),
        patch("standard_tooling.bin.docker_cache.find_cached_image", return_value=None),
    ):
        assert main(["clean"]) == 0
    assert "No cached image" in capsys.readouterr().out


# -- clean-all subcommand -----------------------------------------------------


def test_clean_all(capsys: pytest.CaptureFixture[str]) -> None:
    mock_result = MagicMock(
        returncode=0,
        stdout="ghcr.io/r/dev-go:1.26--feat-42--abc\nghcr.io/r/dev-python:3.14\n",
    )
    with patch("standard_tooling.bin.docker_cache.subprocess.run", return_value=mock_result):
        assert main(["clean-all"]) == 0
    assert "1 cached image" in capsys.readouterr().out
