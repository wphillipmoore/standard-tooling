"""Tests for standard_tooling.lib.docker_cache."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from standard_tooling.lib.docker_cache import (
    _sanitize_branch,
    cache_image_tag,
    cache_sensitive_files,
    clean_branch_images,
    compute_cache_hash,
    ensure_cached_image,
    find_cached_image,
)

if TYPE_CHECKING:
    from pathlib import Path


# -- cache_sensitive_files ----------------------------------------------------


def test_cache_files_python(tmp_path: Path) -> None:
    (tmp_path / "uv.lock").write_text("lock\n")
    (tmp_path / "st-config.toml").write_text("[standard-tooling]\n")
    files = cache_sensitive_files(tmp_path, "python")
    names = [f.name for f in files]
    assert "uv.lock" in names
    assert "st-config.toml" in names


def test_cache_files_go(tmp_path: Path) -> None:
    (tmp_path / "go.sum").write_text("sum\n")
    (tmp_path / "st-config.toml").write_text("[standard-tooling]\n")
    files = cache_sensitive_files(tmp_path, "go")
    names = [f.name for f in files]
    assert "go.sum" in names
    assert "st-config.toml" in names


def test_cache_files_unknown_language(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text("[standard-tooling]\n")
    files = cache_sensitive_files(tmp_path, "")
    assert len(files) == 1
    assert files[0].name == "st-config.toml"


def test_cache_files_missing_lockfile(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text("[standard-tooling]\n")
    files = cache_sensitive_files(tmp_path, "go")
    assert len(files) == 1
    assert files[0].name == "st-config.toml"


# -- compute_cache_hash -------------------------------------------------------


def test_same_content_same_hash(tmp_path: Path) -> None:
    (tmp_path / "a.toml").write_text("x")
    (tmp_path / "b.toml").write_text("y")
    h1 = compute_cache_hash([tmp_path / "a.toml", tmp_path / "b.toml"])
    h2 = compute_cache_hash([tmp_path / "a.toml", tmp_path / "b.toml"])
    assert h1 == h2


def test_different_content_different_hash(tmp_path: Path) -> None:
    (tmp_path / "a.toml").write_text("x")
    h1 = compute_cache_hash([tmp_path / "a.toml"])
    (tmp_path / "a.toml").write_text("y")
    h2 = compute_cache_hash([tmp_path / "a.toml"])
    assert h1 != h2


def test_hash_is_8_chars(tmp_path: Path) -> None:
    (tmp_path / "f").write_text("content")
    h = compute_cache_hash([tmp_path / "f"])
    assert len(h) == 8


# -- _sanitize_branch ---------------------------------------------------------


def test_sanitize_branch_slashes() -> None:
    assert _sanitize_branch("feature/362-decouple") == "feature-362-decouple"


def test_sanitize_branch_special_chars() -> None:
    assert _sanitize_branch("fix/a@b#c") == "fix-a-b-c"


# -- cache_image_tag ----------------------------------------------------------


def test_cache_image_tag_format() -> None:
    tag = cache_image_tag(
        "ghcr.io/wphillipmoore/dev-go:1.26",
        "feature/42-thing",
        "abcd1234",
    )
    assert tag == "ghcr.io/wphillipmoore/dev-go:1.26--feature-42-thing--abcd1234"


# -- find_cached_image --------------------------------------------------------


def test_find_cached_image_hit() -> None:
    docker_output = (
        "ghcr.io/wphillipmoore/dev-go:1.26--feature-42-thing--abcd1234\n"
        "ghcr.io/wphillipmoore/dev-python:3.14\n"
    )
    mock_result = MagicMock(returncode=0, stdout=docker_output)
    with patch("standard_tooling.lib.docker_cache.subprocess.run", return_value=mock_result):
        result = find_cached_image("ghcr.io/wphillipmoore/dev-go:1.26", "feature/42-thing")
    assert result is not None
    assert result[0] == "ghcr.io/wphillipmoore/dev-go:1.26--feature-42-thing--abcd1234"
    assert result[1] == "abcd1234"


def test_find_cached_image_miss() -> None:
    docker_output = "ghcr.io/wphillipmoore/dev-python:3.14\n"
    mock_result = MagicMock(returncode=0, stdout=docker_output)
    with patch("standard_tooling.lib.docker_cache.subprocess.run", return_value=mock_result):
        result = find_cached_image("ghcr.io/wphillipmoore/dev-go:1.26", "feature/42-thing")
    assert result is None


def test_find_cached_image_docker_error() -> None:
    mock_result = MagicMock(returncode=1, stdout="")
    with patch("standard_tooling.lib.docker_cache.subprocess.run", return_value=mock_result):
        assert find_cached_image("img:1", "branch") is None


# -- ensure_cached_image ------------------------------------------------------


def test_ensure_returns_base_for_python(tmp_path: Path) -> None:
    assert ensure_cached_image(tmp_path, "python", "img:1") == "img:1"


def test_ensure_returns_base_when_no_files(tmp_path: Path) -> None:
    with patch("standard_tooling.lib.git.current_branch", return_value="feature/42"):
        assert ensure_cached_image(tmp_path, "go", "img:1") == "img:1"


def test_ensure_returns_existing_cache_on_hash_match(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text('[standard-tooling]\ntag = "v1.4"\n')
    cached_tag = "ghcr.io/r/dev-go:1.26--feature-42--"
    files = cache_sensitive_files(tmp_path, "go")
    expected_hash = compute_cache_hash(files)
    full_tag = cached_tag + expected_hash

    with (
        patch("standard_tooling.lib.git.current_branch") as mock_branch,
        patch(
            "standard_tooling.lib.docker_cache.find_cached_image",
            return_value=(full_tag, expected_hash),
        ),
    ):
        mock_branch.return_value = "feature/42"
        result = ensure_cached_image(tmp_path, "go", "ghcr.io/r/dev-go:1.26")
    assert result == full_tag


def test_ensure_rebuilds_on_hash_mismatch(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text('[standard-tooling]\ntag = "v1.4"\n')
    stale_tag = "ghcr.io/r/dev-go:1.26--feature-42--oldold00"
    new_tag = "ghcr.io/r/dev-go:1.26--feature-42--"

    with (
        patch("standard_tooling.lib.git.current_branch") as mock_branch,
        patch(
            "standard_tooling.lib.docker_cache.find_cached_image",
            return_value=(stale_tag, "oldold00"),
        ),
        patch("standard_tooling.lib.docker_cache.subprocess.run") as mock_run,
        patch(
            "standard_tooling.lib.docker_cache._build_cached_image",
        ) as mock_build,
    ):
        mock_branch.return_value = "feature/42"
        files = cache_sensitive_files(tmp_path, "go")
        expected_hash = compute_cache_hash(files)
        expected_tag = new_tag + expected_hash
        mock_build.return_value = expected_tag

        result = ensure_cached_image(tmp_path, "go", "ghcr.io/r/dev-go:1.26")
    assert result == expected_tag
    # Stale image should have been removed.
    mock_run.assert_called_once()
    assert stale_tag in mock_run.call_args[0][0]


def test_ensure_builds_on_cache_miss(tmp_path: Path) -> None:
    (tmp_path / "st-config.toml").write_text('[standard-tooling]\ntag = "v1.4"\n')

    with (
        patch("standard_tooling.lib.git.current_branch") as mock_branch,
        patch(
            "standard_tooling.lib.docker_cache.find_cached_image",
            return_value=None,
        ),
        patch(
            "standard_tooling.lib.docker_cache._build_cached_image",
            return_value="new:tag",
        ) as mock_build,
    ):
        mock_branch.return_value = "feature/42"
        result = ensure_cached_image(tmp_path, "go", "ghcr.io/r/dev-go:1.26")
    assert result == "new:tag"
    mock_build.assert_called_once()


# -- clean_branch_images ------------------------------------------------------


def test_clean_branch_images_removes_matching() -> None:
    docker_output = (
        "ghcr.io/r/dev-go:1.26--feature-42-thing--abcd1234\n"
        "ghcr.io/r/dev-base:latest--feature-42-thing--efgh5678\n"
        "ghcr.io/r/dev-python:3.14\n"
    )
    mock_result = MagicMock(returncode=0, stdout=docker_output)
    calls = []

    def capture_run(cmd, **kwargs):  # noqa: ANN001, ANN003
        calls.append(cmd)
        return mock_result

    with patch("standard_tooling.lib.docker_cache.subprocess.run", side_effect=capture_run):
        removed = clean_branch_images("feature/42-thing")
    assert removed == 2


def test_clean_branch_images_none_found() -> None:
    mock_result = MagicMock(returncode=0, stdout="ghcr.io/r/dev-python:3.14\n")
    with patch("standard_tooling.lib.docker_cache.subprocess.run", return_value=mock_result):
        assert clean_branch_images("feature/99-other") == 0
