"""Tests for standard_tooling.bin.finalize_repo."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.finalize_repo import main, parse_args

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.target_branch == "develop"
    assert args.dry_run is False


def test_parse_args_custom() -> None:
    args = parse_args(["--target-branch", "main", "--dry-run"])
    assert args.target_branch == "main"
    assert args.dry_run is True


def _make_profile(tmp_path: Path, model: str) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "repository-standards.md").write_text(
        f"## Repository profile\n\n- branching_model: {model}\n"
    )


def test_main_library_release(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.finalize_repo.git.current_branch", return_value="feature/x"),
        patch("standard_tooling.bin.finalize_repo.git.run") as mock_run,
        patch(
            "standard_tooling.bin.finalize_repo.git.merged_branches",
            return_value=["feature/x", "develop"],
        ),
    ):
        result = main([])
    assert result == 0
    mock_run.assert_any_call("checkout", "develop")
    mock_run.assert_any_call("branch", "-d", "feature/x")


def test_main_already_on_target(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.finalize_repo.git.current_branch", return_value="develop"),
        patch("standard_tooling.bin.finalize_repo.git.run"),
        patch("standard_tooling.bin.finalize_repo.git.merged_branches", return_value=[]),
    ):
        result = main([])
    assert result == 0


def test_main_dry_run(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.finalize_repo.git.current_branch", return_value="feature/x"),
        patch("standard_tooling.bin.finalize_repo.git.run") as mock_git_run,
        patch(
            "standard_tooling.bin.finalize_repo.git.merged_branches",
            return_value=["feature/x"],
        ),
    ):
        result = main(["--dry-run"])
    assert result == 0
    mock_git_run.assert_not_called()


def test_main_no_profile(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.finalize_repo.git.current_branch", return_value="develop"),
        patch("standard_tooling.bin.finalize_repo.git.run"),
        patch("standard_tooling.bin.finalize_repo.git.merged_branches", return_value=[]),
    ):
        result = main([])
    assert result == 0


def test_main_unrecognized_model(tmp_path: Path) -> None:
    _make_profile(tmp_path, "unknown-model")
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
    ):
        result = main([])
    assert result == 1


def test_main_application_promotion(tmp_path: Path) -> None:
    _make_profile(tmp_path, "application-promotion")
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.finalize_repo.git.current_branch", return_value="develop"),
        patch("standard_tooling.bin.finalize_repo.git.run"),
        patch(
            "standard_tooling.bin.finalize_repo.git.merged_branches",
            return_value=["develop", "release", "main", "feature/y"],
        ),
    ):
        result = main([])
    assert result == 0


def test_main_docs_single_branch(tmp_path: Path) -> None:
    _make_profile(tmp_path, "docs-single-branch")
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.finalize_repo.git.current_branch", return_value="develop"),
        patch("standard_tooling.bin.finalize_repo.git.run"),
        patch("standard_tooling.bin.finalize_repo.git.merged_branches", return_value=[]),
    ):
        result = main([])
    assert result == 0


def test_main_no_deleted_branches(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch("standard_tooling.bin.finalize_repo.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.finalize_repo.git.current_branch", return_value="develop"),
        patch("standard_tooling.bin.finalize_repo.git.run"),
        patch("standard_tooling.bin.finalize_repo.git.merged_branches", return_value=["develop"]),
    ):
        result = main([])
    assert result == 0
