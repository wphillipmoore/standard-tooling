"""Tests for standard_tooling.lib.config."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from standard_tooling.lib.config import ConfigError, read_config, read_st_config, st_install_tag

if TYPE_CHECKING:
    from pathlib import Path


# -- read_st_config -----------------------------------------------------------


def test_read_valid_config(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text('[standard-tooling]\ntag = "v1.4"\n')
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
    (tmp_path / "st-config.toml").write_text('[standard-tooling]\ntag = "v1.4"\n')
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
    (tmp_path / "st-config.toml").write_text("[standard-tooling]\nother = 1\n")
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(SystemExit, match="missing 'standard-tooling.tag'"),
    ):
        st_install_tag(tmp_path)


def test_env_override(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text('[standard-tooling]\ntag = "v1.4"\n')
    with patch.dict("os.environ", {"ST_DOCKER_INSTALL_TAG": "v2.0"}, clear=True):
        assert st_install_tag(tmp_path) == "v2.0"


def test_env_override_skips_file_read(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"ST_DOCKER_INSTALL_TAG": "v2.0"}, clear=True):
        assert st_install_tag(tmp_path) == "v2.0"


# -- read_config (standard-tooling.toml) --------------------------------------

_VALID_TOML = """\
[project]
repository-type = "library"
versioning-scheme = "semver"
branching-model = "library-release"
release-model = "tagged-release"
primary-language = "python"

[project.co-authors]
claude = "Co-Authored-By: user-claude <111+user-claude@users.noreply.github.com>"

[dependencies]
standard-tooling = "v1.4"
"""


def test_read_config_valid(tmp_path: Path) -> None:
    (tmp_path / "standard-tooling.toml").write_text(_VALID_TOML)
    cfg = read_config(tmp_path)
    assert cfg.project.repository_type == "library"
    assert cfg.project.versioning_scheme == "semver"
    assert cfg.project.branching_model == "library-release"
    assert cfg.project.release_model == "tagged-release"
    assert cfg.project.primary_language == "python"
    assert "claude" in cfg.project.co_authors
    assert "user-claude" in cfg.project.co_authors["claude"]
    assert cfg.dependencies["standard-tooling"] == "v1.4"


def test_read_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="standard-tooling.toml"):
        read_config(tmp_path)


def test_read_config_invalid_toml(tmp_path: Path) -> None:
    (tmp_path / "standard-tooling.toml").write_text("[invalid\n")
    with pytest.raises(ConfigError, match="not valid TOML"):
        read_config(tmp_path)


def test_read_config_missing_project_field(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace('primary-language = "python"\n', "")
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="primary-language"):
        read_config(tmp_path)


def test_read_config_invalid_enum(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace('"library"', '"banana"')
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="repository-type.*banana"):
        read_config(tmp_path)


def test_read_config_malformed_co_author(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace(
        'claude = "Co-Authored-By: user-claude <111+user-claude@users.noreply.github.com>"',
        'claude = "not a valid trailer"',
    )
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="co-author.*claude"):
        read_config(tmp_path)


def test_read_config_missing_dependencies_key(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace('standard-tooling = "v1.4"', 'other = "v1.0"')
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="standard-tooling"):
        read_config(tmp_path)


def test_read_config_no_co_authors(tmp_path: Path) -> None:
    lines = [
        ln
        for ln in _VALID_TOML.splitlines(keepends=True)
        if "co-authors" not in ln.lower() and "claude" not in ln
    ]
    (tmp_path / "standard-tooling.toml").write_text("".join(lines))
    cfg = read_config(tmp_path)
    assert cfg.project.co_authors == {}
