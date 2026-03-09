"""Tests for standard_tooling.bin.docker_run."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.docker_run import main

if TYPE_CHECKING:
    from pathlib import Path


# -- argument parsing ---------------------------------------------------------


def test_no_args() -> None:
    assert main([]) == 1


def test_no_command_after_separator() -> None:
    assert main(["--"]) == 1


# -- GH_TOKEN assertion -------------------------------------------------------


def test_missing_gh_token(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.docker_run.git.repo_root", return_value=tmp_path),
        patch.dict("os.environ", {}, clear=True),
    ):
        assert main(["--", "echo", "hi"]) == 1


# -- image selection ----------------------------------------------------------


def test_fallback_image_no_language(tmp_path: Path) -> None:
    env = {"GH_TOKEN": "tok"}
    with (
        patch("standard_tooling.bin.docker_run.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_run.assert_docker_available"),
        patch("standard_tooling.bin.docker_run.os.execvp") as mock_exec,
        patch.dict("os.environ", env, clear=True),
    ):
        main(["--", "echo", "hi"])
    args = mock_exec.call_args[0][1]
    assert "ghcr.io/wphillipmoore/dev-docs:latest" in args


def test_language_detected_image(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    env = {"GH_TOKEN": "tok"}
    with (
        patch("standard_tooling.bin.docker_run.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_run.assert_docker_available"),
        patch("standard_tooling.bin.docker_run.os.execvp") as mock_exec,
        patch.dict("os.environ", env, clear=True),
    ):
        main(["--", "echo", "hi"])
    args = mock_exec.call_args[0][1]
    assert "ghcr.io/wphillipmoore/dev-python:3.14" in args


def test_env_image_override(tmp_path: Path) -> None:
    env = {"GH_TOKEN": "tok", "DOCKER_DEV_IMAGE": "custom:img"}
    with (
        patch("standard_tooling.bin.docker_run.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_run.assert_docker_available"),
        patch("standard_tooling.bin.docker_run.os.execvp") as mock_exec,
        patch.dict("os.environ", env, clear=True),
    ):
        main(["--", "echo", "hi"])
    args = mock_exec.call_args[0][1]
    assert "custom:img" in args


# -- command passthrough ------------------------------------------------------


def test_command_after_separator(tmp_path: Path) -> None:
    env = {"GH_TOKEN": "tok"}
    with (
        patch("standard_tooling.bin.docker_run.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_run.assert_docker_available"),
        patch("standard_tooling.bin.docker_run.os.execvp") as mock_exec,
        patch.dict("os.environ", env, clear=True),
    ):
        main(["--", "st-prepare-release", "--issue", "42"])
    args = mock_exec.call_args[0][1]
    assert args[-3:] == ["st-prepare-release", "--issue", "42"]


def test_command_without_separator(tmp_path: Path) -> None:
    env = {"GH_TOKEN": "tok"}
    with (
        patch("standard_tooling.bin.docker_run.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_run.assert_docker_available"),
        patch("standard_tooling.bin.docker_run.os.execvp") as mock_exec,
        patch.dict("os.environ", env, clear=True),
    ):
        main(["echo", "hi"])
    args = mock_exec.call_args[0][1]
    assert args[-2:] == ["echo", "hi"]


# -- execvp call --------------------------------------------------------------


def test_calls_execvp(tmp_path: Path) -> None:
    env = {"GH_TOKEN": "tok"}
    with (
        patch("standard_tooling.bin.docker_run.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.docker_run.assert_docker_available"),
        patch("standard_tooling.bin.docker_run.os.execvp") as mock_exec,
        patch.dict("os.environ", env, clear=True),
    ):
        main(["--", "cmd"])
    mock_exec.assert_called_once()
    assert mock_exec.call_args[0][0] == "docker"
