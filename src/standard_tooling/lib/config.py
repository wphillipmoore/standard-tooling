"""Read per-repo ``st-config.toml`` configuration."""

from __future__ import annotations

import os
import tomllib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

_CONFIG_FILE = "st-config.toml"


def read_st_config(repo_root: Path) -> dict[str, Any]:
    """Parse and return the contents of ``st-config.toml``."""
    config_path = repo_root / _CONFIG_FILE
    if not config_path.is_file():
        raise SystemExit(
            f"ERROR: {_CONFIG_FILE} not found at {repo_root}.\n"
            f"Every repo must have an {_CONFIG_FILE}."
        )
    try:
        with config_path.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"ERROR: {_CONFIG_FILE} at {repo_root} is not valid TOML: {exc}") from exc


def st_install_tag(repo_root: Path) -> str:
    """Return the ``standard-tooling.tag`` value for runtime install.

    Checks ``ST_DOCKER_INSTALL_TAG`` env var first (override).
    """
    override = os.environ.get("ST_DOCKER_INSTALL_TAG")
    if override:
        return override
    config = read_st_config(repo_root)
    st = config.get("standard-tooling", {})
    tag = st.get("tag")
    if not tag:
        raise SystemExit(f"ERROR: {_CONFIG_FILE} missing 'standard-tooling.tag' field.")
    return str(tag)
