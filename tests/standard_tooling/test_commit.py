"""Tests for standard_tooling.bin.commit."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from standard_tooling.bin.commit import parse_args

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_args_required() -> None:
    args = parse_args(["--type", "feat", "--message", "add thing", "--agent", "claude"])
    assert args.commit_type == "feat"
    assert args.message == "add thing"
    assert args.agent == "claude"
    assert args.scope == ""
    assert args.body == ""


def test_parse_args_with_scope_and_body() -> None:
    args = parse_args([
        "--type", "fix", "--scope", "lint",
        "--message", "correct regex", "--body", "Fixed edge case",
        "--agent", "codex",
    ])
    assert args.commit_type == "fix"
    assert args.scope == "lint"
    assert args.body == "Fixed edge case"


def test_parse_args_invalid_type() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--type", "invalid", "--message", "x", "--agent", "claude"])


def test_main_no_staged_changes(tmp_path: Path) -> None:
    from standard_tooling.bin.commit import main

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
