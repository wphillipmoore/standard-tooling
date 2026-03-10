"""Tests for standard_tooling.lib.docker."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from standard_tooling.lib.docker import (
    _FALLBACK_IMAGE,
    assert_docker_available,
    build_docker_args,
    default_image,
    detect_language,
)

if TYPE_CHECKING:
    from pathlib import Path


# -- detect_language ----------------------------------------------------------


def test_detect_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    assert detect_language(tmp_path) == "python"


def test_detect_ruby(tmp_path: Path) -> None:
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    assert detect_language(tmp_path) == "ruby"


def test_detect_go(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example\n")
    assert detect_language(tmp_path) == "go"


def test_detect_rust(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\n")
    assert detect_language(tmp_path) == "rust"


def test_detect_java_pom(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("<project/>\n")
    assert detect_language(tmp_path) == "java"


def test_detect_java_mvnw(tmp_path: Path) -> None:
    (tmp_path / "mvnw").write_text("#!/bin/bash\n")
    assert detect_language(tmp_path) == "java"


def test_detect_none(tmp_path: Path) -> None:
    assert detect_language(tmp_path) == ""


def test_detect_ruby_priority(tmp_path: Path) -> None:
    (tmp_path / "Gemfile").write_text("")
    (tmp_path / "pyproject.toml").write_text("")
    assert detect_language(tmp_path) == "ruby"


# -- default_image ------------------------------------------------------------


def test_default_image_known_lang() -> None:
    assert "dev-python" in default_image("python")


def test_default_image_unknown_no_fallback() -> None:
    assert default_image("unknown") == ""


def test_default_image_unknown_with_fallback() -> None:
    assert default_image("unknown", fallback=True) == _FALLBACK_IMAGE


def test_default_image_empty_with_fallback() -> None:
    assert default_image("", fallback=True) == _FALLBACK_IMAGE


# -- build_docker_args --------------------------------------------------------


def test_build_docker_args_basic(tmp_path: Path) -> None:
    with patch.dict("os.environ", {}, clear=True):
        args = build_docker_args(tmp_path, "img:1", ["echo", "hello"])
    assert args[:3] == ["docker", "run", "--rm"]
    assert f"{tmp_path}:/workspace" in args
    assert "img:1" in args
    assert args[-2:] == ["echo", "hello"]


def test_build_docker_args_network(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"DOCKER_NETWORK": "mynet"}, clear=True):
        args = build_docker_args(tmp_path, "img:1", ["cmd"])
    assert "--network" in args
    assert "mynet" in args


def test_build_docker_args_extra_volumes(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"DOCKER_EXTRA_VOLUMES": "/a:/b;/c:/d"}, clear=True):
        args = build_docker_args(tmp_path, "img:1", ["cmd"])
    assert "/a:/b" in args
    assert "/c:/d" in args


def test_build_docker_args_empty_extra_volumes(tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    with (
        patch.dict("os.environ", {"DOCKER_EXTRA_VOLUMES": ";"}, clear=True),
        patch("standard_tooling.lib.docker.Path.home", return_value=fake_home),
    ):
        args = build_docker_args(tmp_path, "img:1", ["cmd"])
    v_indices = [i for i, a in enumerate(args) if a == "-v"]
    assert len(v_indices) == 1


def test_build_docker_args_env_passthrough(tmp_path: Path) -> None:
    env = {"MQ_HOST": "localhost", "GH_TOKEN": "tok", "GITHUB_SHA": "abc"}
    with patch.dict("os.environ", env, clear=True):
        args = build_docker_args(tmp_path, "img:1", ["cmd"])
    assert "MQ_HOST" in args
    assert "GH_TOKEN" in args
    assert "GITHUB_SHA" in args


def test_build_docker_args_no_unrelated_env(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"HOME": "/home/user"}, clear=True):
        args = build_docker_args(tmp_path, "img:1", ["cmd"])
    assert "HOME" not in args


def test_build_docker_args_mounts_gitconfig(tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    gitconfig = fake_home / ".gitconfig"
    gitconfig.write_text("[user]\n\tname = Test\n")
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("standard_tooling.lib.docker.Path.home", return_value=fake_home),
    ):
        args = build_docker_args(tmp_path, "img:1", ["cmd"])
    assert f"{gitconfig}:/root/.gitconfig:ro" in args


def test_build_docker_args_no_gitconfig(tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("standard_tooling.lib.docker.Path.home", return_value=fake_home),
    ):
        args = build_docker_args(tmp_path, "img:1", ["cmd"])
    assert all("/root/.gitconfig" not in a for a in args)


# -- assert_docker_available --------------------------------------------------


def test_assert_docker_available_success() -> None:
    mock_result = MagicMock(returncode=0)
    with patch("standard_tooling.lib.docker.subprocess.run", return_value=mock_result):
        assert_docker_available()  # should not raise


def test_assert_docker_available_failure() -> None:
    mock_result = MagicMock(returncode=1)
    with (
        patch("standard_tooling.lib.docker.subprocess.run", return_value=mock_result),
        pytest.raises(SystemExit),
    ):
        assert_docker_available()


def test_assert_docker_available_not_installed() -> None:
    with (
        patch("standard_tooling.lib.docker.subprocess.run", side_effect=FileNotFoundError),
        pytest.raises(SystemExit),
    ):
        assert_docker_available()


def test_assert_docker_available_timeout() -> None:
    with (
        patch(
            "standard_tooling.lib.docker.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="docker info", timeout=10),
        ),
        pytest.raises(SystemExit),
    ):
        assert_docker_available()
