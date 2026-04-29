"""Tests for standard_tooling.lib.config."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from standard_tooling.lib.config import read_st_config, st_install_tag

if TYPE_CHECKING:
    from pathlib import Path


# -- read_st_config -----------------------------------------------------------


def test_read_valid_config(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text(
        '[standard-tooling]\ntag = "v1.4"\n'
    )
    config = read_st_config(tmp_path)
    assert config["standard-tooling"]["tag"] == "v1.4"


def test_read_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="st-config.toml not found"):
        read_st_config(tmp_path)


def test_read_empty_file(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text("")
    assert read_st_config(tmp_path) == {}


def test_read_malformed_toml(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text("[invalid\n")
    with pytest.raises(SystemExit):
        read_st_config(tmp_path)


# -- st_install_tag -----------------------------------------------------------


def test_tag_from_config(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text(
        '[standard-tooling]\ntag = "v1.4"\n'
    )
    with patch.dict("os.environ", {}, clear=True):
        assert st_install_tag(tmp_path) == "v1.4"


def test_tag_missing_section(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text("[other]\nkey = 1\n")
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(SystemExit, match="missing 'standard-tooling.tag'"),
    ):
        st_install_tag(tmp_path)


def test_tag_missing_field(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text(
        "[standard-tooling]\nother = 1\n"
    )
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(SystemExit, match="missing 'standard-tooling.tag'"),
    ):
        st_install_tag(tmp_path)


def test_env_override(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text(
        '[standard-tooling]\ntag = "v1.4"\n'
    )
    with patch.dict("os.environ", {"ST_DOCKER_INSTALL_TAG": "v2.0"}, clear=True):
        assert st_install_tag(tmp_path) == "v2.0"


def test_env_override_skips_file_read(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"ST_DOCKER_INSTALL_TAG": "v2.0"}, clear=True):
        assert st_install_tag(tmp_path) == "v2.0"
