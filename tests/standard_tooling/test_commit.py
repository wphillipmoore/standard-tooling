"""Tests for standard_tooling.bin.commit."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from standard_tooling.bin.commit import main, parse_args


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
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
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
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
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
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
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
