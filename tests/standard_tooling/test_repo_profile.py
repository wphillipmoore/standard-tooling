"""Tests for standard_tooling.lib.repo_profile."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from standard_tooling.lib.repo_profile import (
    read_co_authors,
    read_profile,
    resolve_co_author,
)

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_PROFILE = """\
# Example Repository Standards

## Table of Contents

- [AI co-authors](#ai-co-authors)
- [Repository profile](#repository-profile)

## AI co-authors

- Co-Authored-By: user-codex <111+user-codex@users.noreply.github.com>
- Co-Authored-By: user-claude <222+user-claude@users.noreply.github.com>

## Repository profile

- repository_type: library
- versioning_scheme: semver
- branching_model: library-release
- release_model: tagged-release
- supported_release_lines: 1
- primary_language: python
"""


@pytest.fixture()
def profile_dir(tmp_path: Path) -> Path:
    """Create a temp directory with a sample repository-standards.md."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "repository-standards.md").write_text(SAMPLE_PROFILE)
    return tmp_path


def test_read_profile(profile_dir: Path) -> None:
    profile = read_profile(profile_dir)
    assert profile.repository_type == "library"
    assert profile.versioning_scheme == "semver"
    assert profile.branching_model == "library-release"
    assert profile.release_model == "tagged-release"
    assert profile.supported_release_lines == "1"
    assert profile.primary_language == "python"


def test_read_profile_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Repository profile not found"):
        read_profile(tmp_path)


def test_read_co_authors(profile_dir: Path) -> None:
    authors = read_co_authors(profile_dir)
    assert len(authors) == 2
    assert "user-codex" in authors[0]
    assert "user-claude" in authors[1]


def test_read_co_authors_missing_file(tmp_path: Path) -> None:
    assert read_co_authors(tmp_path) == []


def test_resolve_co_author_claude(profile_dir: Path) -> None:
    identity = resolve_co_author("claude", profile_dir)
    assert "user-claude" in identity
    assert "Co-Authored-By:" in identity


def test_resolve_co_author_codex(profile_dir: Path) -> None:
    identity = resolve_co_author("codex", profile_dir)
    assert "user-codex" in identity


def test_resolve_co_author_unknown(profile_dir: Path) -> None:
    with pytest.raises(SystemExit, match="No approved identity found"):
        resolve_co_author("unknown-agent", profile_dir)
