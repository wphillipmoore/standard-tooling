"""Tests for standard_tooling.bin.submit_pr."""

from __future__ import annotations

import pytest

from standard_tooling.bin.submit_pr import _resolve_issue_ref, parse_args


def test_resolve_plain_number() -> None:
    assert _resolve_issue_ref("42") == "#42"


def test_resolve_cross_repo() -> None:
    assert _resolve_issue_ref("owner/repo#42") == "owner/repo#42"


def test_resolve_invalid() -> None:
    with pytest.raises(SystemExit, match="must be a number"):
        _resolve_issue_ref("bad-ref")


def test_resolve_zero() -> None:
    with pytest.raises(SystemExit, match="must be a number"):
        _resolve_issue_ref("0")


def test_parse_args_required() -> None:
    args = parse_args(["--issue", "42", "--summary", "Fix bug"])
    assert args.issue == "42"
    assert args.summary == "Fix bug"
    assert args.linkage == "Fixes"
    assert args.docs_only is False
    assert args.dry_run is False


def test_parse_args_all_options() -> None:
    args = parse_args([
        "--issue", "owner/repo#10", "--summary", "Add feature",
        "--linkage", "Ref", "--notes", "Tested", "--title", "My PR",
        "--docs-only", "--dry-run",
    ])
    assert args.linkage == "Ref"
    assert args.docs_only is True
    assert args.dry_run is True
