"""Tests for standard_tooling.bin.repo_profile_cli."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.repo_profile_cli import _structural_check, main

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


def _mock_profile_ok() -> patch:
    from standard_tooling.lib.repo_profile import RepoProfile

    return patch(
        "standard_tooling.bin.repo_profile_cli.read_profile",
        return_value=RepoProfile(
            repository_type="library",
            versioning_scheme="semver",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        ),
    )


# -- profile validation ------------------------------------------------------


def test_valid_profile(tmp_path: Path) -> None:
    _write_profile(tmp_path, _VALID_PROFILE)
    with (
        _mock_profile_ok(),
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_missing_profile() -> None:
    with patch(
        "standard_tooling.bin.repo_profile_cli.read_profile",
        side_effect=FileNotFoundError("not found"),
    ):
        assert main() == 2


def test_empty_attribute(tmp_path: Path) -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with (
        patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read,
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        mock_read.return_value = RepoProfile(
            repository_type="library",
            versioning_scheme="semver",
            branching_model="",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1


def test_placeholder_angle_brackets(tmp_path: Path) -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with (
        patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read,
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        mock_read.return_value = RepoProfile(
            repository_type="<choose one>",
            versioning_scheme="semver",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1


def test_placeholder_pipe(tmp_path: Path) -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with (
        patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read,
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        mock_read.return_value = RepoProfile(
            repository_type="library",
            versioning_scheme="semver|calver",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1


def test_multiple_errors(tmp_path: Path) -> None:
    from standard_tooling.lib.repo_profile import RepoProfile

    with (
        patch("standard_tooling.bin.repo_profile_cli.read_profile") as mock_read,
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        mock_read.return_value = RepoProfile(
            repository_type="",
            versioning_scheme="",
            branching_model="library-release",
            release_model="tagged-release",
            supported_release_lines="1",
            primary_language="python",
        )
        assert main() == 1


# -- _structural_check -------------------------------------------------------


def test_structural_valid(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n## Section\n")
    assert _structural_check(str(doc)) is True


def test_structural_no_h1(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("## Section\n\n## Table of Contents\n")
    assert _structural_check(str(doc)) is False


def test_structural_multiple_h1(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n# Another\n\n## Table of Contents\n")
    assert _structural_check(str(doc)) is False


def test_structural_no_toc(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Section\n")
    assert _structural_check(str(doc)) is False


def test_structural_heading_skip(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n#### Skipped\n")
    assert _structural_check(str(doc)) is False


def test_structural_code_fence_ignored(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n```\n# Not a heading\n```\n\n## End\n")
    assert _structural_check(str(doc)) is True


def test_structural_tilde_fence_ignored(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n~~~\n# Not a heading\n~~~\n\n## End\n")
    assert _structural_check(str(doc)) is True


# -- main: structural check integration --------------------------------------


def test_main_readme_structural_fails(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("## No H1\n")
    with (
        _mock_profile_ok(),
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 1


def test_main_readme_structural_passes(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Title\n\n## Table of Contents\n\n## Section\n")
    with (
        _mock_profile_ok(),
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_main_no_readme(tmp_path: Path) -> None:
    with (
        _mock_profile_ok(),
        patch("standard_tooling.bin.repo_profile_cli.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0
