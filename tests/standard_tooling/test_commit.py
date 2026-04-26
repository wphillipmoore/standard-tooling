"""Tests for standard_tooling.bin.commit."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from standard_tooling.bin.commit import main, parse_args

if TYPE_CHECKING:
    from collections.abc import Iterator


@contextlib.contextmanager
def _commit_environment(
    tmp_path: Path,
    *,
    branch: str = "feature/42-test",
    is_main_worktree: bool = False,
    branching_model: str | None = None,
    has_staged: bool = True,
    captured_env: dict[str, str | None] | None = None,
) -> Iterator[None]:
    """Set up mocks for `commit.main()`.

    Defaults represent a happy path: secondary worktree, `library-release`
    profile (branching_model resolves from disk if profile is written),
    valid `feature/42-test` branch, staged changes present.

    `captured_env` (if provided) is updated with the value of
    `os.environ.get("ST_COMMIT_CONTEXT")` at the moment `git.run` is
    invoked, so tests can pin Task 1.2's contract.
    """

    def _capture_run(*args: str) -> None:
        if captured_env is not None and args[:2] == ("commit", "--file"):
            captured_env["ST_COMMIT_CONTEXT"] = os.environ.get("ST_COMMIT_CONTEXT")

    if branching_model is not None:
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "repository-standards.md").write_text(
            f"## Repository profile\n\n- branching_model: {branching_model}\n"
        )

    co_author = "Co-Authored-By: test <test@test.com>"
    with (
        patch("standard_tooling.bin.commit.git.current_branch", return_value=branch),
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.commit.git.is_main_worktree",
            return_value=is_main_worktree,
        ),
        patch(
            "standard_tooling.bin.commit.git.has_staged_changes",
            return_value=has_staged,
        ),
        patch("standard_tooling.bin.commit.git.run", side_effect=_capture_run),
        patch(
            "standard_tooling.bin.commit.repo_profile.resolve_co_author",
            return_value=co_author,
        ),
    ):
        yield


def test_parse_args_required() -> None:
    args = parse_args(["--type", "feat", "--message", "add thing", "--agent", "claude"])
    assert args.commit_type == "feat"
    assert args.message == "add thing"
    assert args.agent == "claude"
    assert args.scope == ""
    assert args.body == ""


def test_parse_args_with_scope_and_body() -> None:
    args = parse_args(
        [
            "--type",
            "fix",
            "--scope",
            "lint",
            "--message",
            "correct regex",
            "--body",
            "Fixed edge case",
            "--agent",
            "codex",
        ]
    )
    assert args.commit_type == "fix"
    assert args.scope == "lint"
    assert args.body == "Fixed edge case"


def test_parse_args_invalid_type() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--type", "invalid", "--message", "x", "--agent", "claude"])


def test_main_no_staged_changes(tmp_path: Path) -> None:
    co_author = "Co-Authored-By: test <test@test.com>"
    with (
        patch("standard_tooling.bin.commit.git.current_branch", return_value="feature/42-x"),
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.commit.git.is_main_worktree",
            return_value=False,
        ),
        patch(
            "standard_tooling.bin.commit.repo_profile.resolve_co_author",
            return_value=co_author,
        ),
        patch(
            "standard_tooling.bin.commit.git.has_staged_changes",
            return_value=False,
        ),
    ):
        result = main(["--type", "feat", "--message", "test", "--agent", "claude"])
    assert result == 1


def test_main_with_staged_changes_no_scope(tmp_path: Path) -> None:
    co_author = "Co-Authored-By: test <test@test.com>"
    commit_file_content = ""

    def capture_run(*args: str) -> None:
        nonlocal commit_file_content
        if args[0] == "commit" and args[1] == "--file":
            commit_file_content = Path(args[2]).read_text(encoding="utf-8")

    with (
        patch("standard_tooling.bin.commit.git.current_branch", return_value="feature/42-x"),
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.commit.git.is_main_worktree",
            return_value=False,
        ),
        patch(
            "standard_tooling.bin.commit.repo_profile.resolve_co_author",
            return_value=co_author,
        ),
        patch("standard_tooling.bin.commit.git.has_staged_changes", return_value=True),
        patch("standard_tooling.bin.commit.git.run", side_effect=capture_run),
    ):
        result = main(["--type", "feat", "--message", "add feature", "--agent", "claude"])
    assert result == 0
    assert commit_file_content.startswith("feat: add feature\n")
    assert co_author in commit_file_content


def test_main_with_scope_and_body(tmp_path: Path) -> None:
    co_author = "Co-Authored-By: test <test@test.com>"
    commit_file_content = ""

    def capture_run(*args: str) -> None:
        nonlocal commit_file_content
        if args[0] == "commit" and args[1] == "--file":
            commit_file_content = Path(args[2]).read_text(encoding="utf-8")

    with (
        patch("standard_tooling.bin.commit.git.current_branch", return_value="feature/42-x"),
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.commit.git.is_main_worktree",
            return_value=False,
        ),
        patch(
            "standard_tooling.bin.commit.repo_profile.resolve_co_author",
            return_value=co_author,
        ),
        patch("standard_tooling.bin.commit.git.has_staged_changes", return_value=True),
        patch("standard_tooling.bin.commit.git.run", side_effect=capture_run),
    ):
        result = main(
            [
                "--type",
                "fix",
                "--scope",
                "lint",
                "--message",
                "correct regex",
                "--body",
                "Fixed edge case",
                "--agent",
                "claude",
            ]
        )
    assert result == 0
    assert "fix(lint): correct regex" in commit_file_content
    assert "Fixed edge case" in commit_file_content
    assert co_author in commit_file_content


# --------------------------------------------------------------------------
# Task 1.1 — branch / context validation
# --------------------------------------------------------------------------
#
# Five checks ported from src/standard_tooling/bin/pre_commit_hook.py into
# st-commit. Each check has a rejection-path and a happy-path test.
# Reference: docs/specs/host-level-tool.md "Migration / standard-tooling
# itself" step 1; docs/plans/host-level-tool-plan.md Task 1.1.

_DEFAULT_ARGS = ["--type", "feat", "--message", "test", "--agent", "claude"]


# Check 1: detached HEAD


def test_validate_rejects_detached_head(tmp_path: Path) -> None:
    with _commit_environment(tmp_path, branch="HEAD"):
        assert main(_DEFAULT_ARGS) == 1


def test_validate_admits_normal_branch(tmp_path: Path) -> None:
    with _commit_environment(tmp_path, branch="feature/42-test"):
        assert main(_DEFAULT_ARGS) == 0


# Check 2: protected branches


@pytest.mark.parametrize("branch", ["develop", "release", "main"])
def test_validate_rejects_protected_branches(tmp_path: Path, branch: str) -> None:
    with _commit_environment(tmp_path, branch=branch):
        assert main(_DEFAULT_ARGS) == 1


# Check 3: branch prefix against branching_model


def test_validate_rejects_invalid_prefix_for_library_release(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path, branch="promotion/42-deploy", branching_model="library-release"
    ):
        assert main(_DEFAULT_ARGS) == 1


def test_validate_admits_release_branch_for_library_release(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path, branch="release/1.2.3", branching_model="library-release"
    ):
        assert main(_DEFAULT_ARGS) == 0


def test_validate_rejects_hotfix_for_docs_single_branch(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path, branch="hotfix/42-urgent", branching_model="docs-single-branch"
    ):
        assert main(_DEFAULT_ARGS) == 1


def test_validate_admits_promotion_for_application_promotion(tmp_path: Path) -> None:
    # promotion branches are allowed and not subject to the issue-number rule.
    with _commit_environment(
        tmp_path, branch="promotion/42-deploy", branching_model="application-promotion"
    ):
        assert main(_DEFAULT_ARGS) == 0


def test_validate_rejects_unknown_branching_model(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path, branch="feature/42-thing", branching_model="bogus-model"
    ):
        assert main(_DEFAULT_ARGS) == 1


def test_validate_falls_back_when_no_profile(tmp_path: Path) -> None:
    # No profile written; falls back to feature|bugfix|chore.
    with _commit_environment(tmp_path, branch="feature/42-test"):
        assert main(_DEFAULT_ARGS) == 0


def test_validate_fallback_rejects_hotfix(tmp_path: Path) -> None:
    with _commit_environment(tmp_path, branch="hotfix/42-urgent"):
        assert main(_DEFAULT_ARGS) == 1


# Check 4: issue number in branch name


def test_validate_rejects_missing_issue_number(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path, branch="feature/no-number", branching_model="library-release"
    ):
        assert main(_DEFAULT_ARGS) == 1


def test_validate_admits_bugfix_with_issue(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path, branch="bugfix/99-fix-parsing", branching_model="library-release"
    ):
        assert main(_DEFAULT_ARGS) == 0


def test_validate_admits_chore_with_issue(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path, branch="chore/5-update-deps", branching_model="library-release"
    ):
        assert main(_DEFAULT_ARGS) == 0


def test_validate_rejects_application_promotion_hotfix_without_issue(tmp_path: Path) -> None:
    with _commit_environment(
        tmp_path,
        branch="hotfix/no-number",
        branching_model="application-promotion",
    ):
        assert main(_DEFAULT_ARGS) == 1


# Check 5: worktree convention — main-tree feature commits forbidden when
# .worktrees/ exists


def test_validate_rejects_main_worktree_feature_commit_when_worktrees_dir(
    tmp_path: Path,
) -> None:
    (tmp_path / ".worktrees").mkdir()
    with _commit_environment(
        tmp_path,
        branch="feature/42-x",
        branching_model="library-release",
        is_main_worktree=True,
    ):
        assert main(_DEFAULT_ARGS) == 1


def test_validate_admits_secondary_worktree_feature_commit(tmp_path: Path) -> None:
    (tmp_path / ".worktrees").mkdir()
    with _commit_environment(
        tmp_path,
        branch="feature/42-x",
        branching_model="library-release",
        is_main_worktree=False,
    ):
        assert main(_DEFAULT_ARGS) == 0


def test_validate_admits_main_worktree_release_commit_when_worktrees_dir(
    tmp_path: Path,
) -> None:
    # release/* is not subject to the worktree-convention check (only
    # feature|bugfix|hotfix|chore are scoped under that rule).
    (tmp_path / ".worktrees").mkdir()
    with _commit_environment(
        tmp_path,
        branch="release/1.2.3",
        branching_model="library-release",
        is_main_worktree=True,
    ):
        assert main(_DEFAULT_ARGS) == 0


def test_validate_admits_main_worktree_feature_commit_without_worktrees_dir(
    tmp_path: Path,
) -> None:
    with _commit_environment(
        tmp_path,
        branch="feature/42-x",
        branching_model="library-release",
        is_main_worktree=True,
    ):
        # No .worktrees/ → the rule does not apply.
        assert main(_DEFAULT_ARGS) == 0


# --------------------------------------------------------------------------
# Task 1.2 — st-commit sets ST_COMMIT_CONTEXT=1 before invoking git commit
# --------------------------------------------------------------------------


def test_st_commit_sets_st_commit_context_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The env-var gate (`.githooks/pre-commit`) reads ST_COMMIT_CONTEXT.
    `st-commit` must set it to "1" before invoking `git commit`, otherwise
    the gate rejects the commit. Contract is documented in
    docs/specs/host-level-tool.md and is load-bearing for the fleet.
    """
    monkeypatch.delenv("ST_COMMIT_CONTEXT", raising=False)
    captured: dict[str, str | None] = {}
    with _commit_environment(
        tmp_path, branch="feature/42-test", captured_env=captured
    ):
        assert main(_DEFAULT_ARGS) == 0
    assert captured.get("ST_COMMIT_CONTEXT") == "1"
