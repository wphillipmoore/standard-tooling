"""Tests for standard_tooling.bin.pre_commit_hook."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from standard_tooling.bin.pre_commit_hook import main

if TYPE_CHECKING:
    from pathlib import Path


def _write_profile(tmp_path: Path, branching_model: str) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "repository-standards.md").write_text(
        f"## Repository profile\n\n- branching_model: {branching_model}\n"
    )


def test_detached_head(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.pre_commit_hook.git.current_branch", return_value="HEAD"),
    ):
        assert main() == 1


@pytest.mark.parametrize("branch", ["develop", "release", "main"])
def test_protected_branch(tmp_path: Path, branch: str) -> None:
    with (
        patch("standard_tooling.bin.pre_commit_hook.git.current_branch", return_value=branch),
    ):
        assert main() == 1


def test_library_release_valid_feature(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/42-add-caching",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_library_release_valid_release(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="release/1.2.3",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_library_release_invalid_prefix(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="promotion/42-deploy",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 1


def test_application_promotion_valid(tmp_path: Path) -> None:
    _write_profile(tmp_path, "application-promotion")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="promotion/42-deploy",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        # promotion branches don't need issue format
        assert main() == 0


def test_docs_single_branch_valid(tmp_path: Path) -> None:
    _write_profile(tmp_path, "docs-single-branch")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/42-add-docs",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_docs_single_branch_invalid_hotfix(tmp_path: Path) -> None:
    _write_profile(tmp_path, "docs-single-branch")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="hotfix/42-urgent",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 1


def test_no_profile_fallback(tmp_path: Path) -> None:
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/42-add-thing",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_no_profile_fallback_rejects_hotfix(tmp_path: Path) -> None:
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="hotfix/42-urgent",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 1


def test_unrecognized_branching_model(tmp_path: Path) -> None:
    _write_profile(tmp_path, "unknown-model")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/42-thing",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 1


def test_missing_issue_number(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/no-issue-number",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 1


def test_bugfix_with_issue(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="bugfix/99-fix-parsing",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_chore_with_issue(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="chore/5-update-deps",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_hotfix_with_issue(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="hotfix/1-critical-fix",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 0


def test_application_promotion_hotfix_needs_issue(tmp_path: Path) -> None:
    _write_profile(tmp_path, "application-promotion")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="hotfix/no-number",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
    ):
        assert main() == 1


def test_main_worktree_feature_commit_refused_when_worktrees_dir_exists(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    (tmp_path / ".worktrees").mkdir()
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/42-add-caching",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.pre_commit_hook.git.is_main_worktree",
            return_value=True,
        ),
    ):
        assert main() == 1


def test_secondary_worktree_feature_commit_allowed(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    (tmp_path / ".worktrees").mkdir()
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/42-add-caching",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.pre_commit_hook.git.is_main_worktree",
            return_value=False,
        ),
    ):
        assert main() == 0


def test_main_worktree_feature_commit_allowed_without_worktrees_dir(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="feature/42-add-caching",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.pre_commit_hook.git.is_main_worktree",
            return_value=True,
        ),
    ):
        assert main() == 0


def test_main_worktree_release_branch_allowed_even_with_worktrees_dir(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    (tmp_path / ".worktrees").mkdir()
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="release/1.2.3",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.pre_commit_hook.git.is_main_worktree",
            return_value=True,
        ),
    ):
        assert main() == 0


def test_main_worktree_bugfix_commit_refused(tmp_path: Path) -> None:
    _write_profile(tmp_path, "library-release")
    (tmp_path / ".worktrees").mkdir()
    with (
        patch(
            "standard_tooling.bin.pre_commit_hook.git.current_branch",
            return_value="bugfix/99-fix-parsing",
        ),
        patch("standard_tooling.bin.pre_commit_hook.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.pre_commit_hook.git.is_main_worktree",
            return_value=True,
        ),
    ):
        assert main() == 1
