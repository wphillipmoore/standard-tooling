"""Tests for standard_tooling.bin.repo_profile_cli."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.repo_profile_cli import main

if TYPE_CHECKING:
    from pathlib import Path

_VALID_PROFILE = """\
## Repository profile

- repository_type: library
- versioning_scheme: semver
- branching_model: library-release
- release_model: tagged-release
- supported_release_lines: 1
- primary_language: python
"""


def _write_profile(tmp_path: Path, content: str) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "repository-standards.md").write_text(content)


def test_valid_profile(tmp_path: Path) -> None:
    _write_profile(tmp_path, _VALID_PROFILE)
    with patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read:
        from standard_tooling.lib.repo_profile import RepoProfile

        mock_read.return_value = RepoProfile(
            repository_type="library",
            versioning_scheme="semver",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 0


def test_missing_profile() -> None:
    with patch(
        "standard_tooling.bin.repo_profile_cli.read_profile",
        side_effect=FileNotFoundError("not found"),
    ):
        assert main() == 2


def test_empty_attribute() -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read:
        mock_read.return_value = RepoProfile(
            repository_type="library",
            versioning_scheme="semver",
            branching_model="",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1


def test_placeholder_angle_brackets() -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read:
        mock_read.return_value = RepoProfile(
            repository_type="<choose one>",
            versioning_scheme="semver",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1


def test_placeholder_pipe() -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read:
        mock_read.return_value = RepoProfile(
            repository_type="library",
            versioning_scheme="semver|calver",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1


def test_multiple_errors() -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read:
        mock_read.return_value = RepoProfile(
            repository_type="",
            versioning_scheme="",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1
