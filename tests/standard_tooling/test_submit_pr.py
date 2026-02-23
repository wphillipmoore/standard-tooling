"""Tests for standard_tooling.bin.submit_pr."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from standard_tooling.bin.submit_pr import (
    _extract_testing_section,
    _resolve_issue_ref,
    main,
    parse_args,
)

if TYPE_CHECKING:
    from pathlib import Path


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
    args = parse_args(
        [
            "--issue",
            "owner/repo#10",
            "--summary",
            "Add feature",
            "--linkage",
            "Ref",
            "--notes",
            "Tested",
            "--title",
            "My PR",
            "--docs-only",
            "--dry-run",
        ]
    )
    assert args.linkage == "Ref"
    assert args.docs_only is True
    assert args.dry_run is True


def test_extract_testing_section_no_template(tmp_path: Path) -> None:
    assert _extract_testing_section(tmp_path) == ""


def test_extract_testing_section_with_template(tmp_path: Path) -> None:
    gh = tmp_path / ".github"
    gh.mkdir()
    (gh / "pull_request_template.md").write_text(
        "## Summary\n\nStuff\n\n## Testing\n\nRun tests\nCheck coverage\n\n## Notes\n\nNone\n"
    )
    result = _extract_testing_section(tmp_path)
    assert "Run tests" in result
    assert "Check coverage" in result
    assert "Notes" not in result


def test_extract_testing_section_testing_at_end(tmp_path: Path) -> None:
    gh = tmp_path / ".github"
    gh.mkdir()
    (gh / "pull_request_template.md").write_text("## Testing\n\nFinal section\n")
    result = _extract_testing_section(tmp_path)
    assert "Final section" in result


def test_main_dry_run(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.submit_pr.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.submit_pr.git.current_branch", return_value="feature/x"),
        patch("standard_tooling.bin.submit_pr.git.read_output", return_value="feat: add thing"),
    ):
        result = main(["--issue", "42", "--summary", "Fix bug", "--dry-run"])
    assert result == 0


def test_main_dry_run_with_title(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.submit_pr.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.submit_pr.git.current_branch", return_value="feature/x"),
    ):
        result = main(
            [
                "--issue",
                "42",
                "--summary",
                "Fix bug",
                "--title",
                "Custom Title",
                "--dry-run",
            ]
        )
    assert result == 0


def test_main_dry_run_release_branch(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.submit_pr.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.submit_pr.git.current_branch",
            return_value="release/1.0.0",
        ),
        patch("standard_tooling.bin.submit_pr.git.read_output", return_value="release: 1.0.0"),
    ):
        result = main(["--issue", "42", "--summary", "Release 1.0.0", "--dry-run"])
    assert result == 0


def test_main_dry_run_docs_only(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.submit_pr.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.submit_pr.git.current_branch", return_value="feature/x"),
        patch(
            "standard_tooling.bin.submit_pr.git.read_output",
            return_value="docs: update README",
        ),
    ):
        result = main(
            [
                "--issue",
                "42",
                "--summary",
                "Update docs",
                "--docs-only",
                "--dry-run",
            ]
        )
    assert result == 0


def test_main_dry_run_docs_only_diff_fallback(tmp_path: Path) -> None:
    call_count = 0

    def mock_read_output(*args: str) -> str:
        nonlocal call_count
        call_count += 1
        if args[0] == "log":
            return "docs: update README"
        if args[0] == "diff" and "develop...HEAD" in " ".join(args):
            raise RuntimeError("no upstream")
        return "README.md"

    with (
        patch("standard_tooling.bin.submit_pr.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.submit_pr.git.current_branch", return_value="feature/x"),
        patch("standard_tooling.bin.submit_pr.git.read_output", side_effect=mock_read_output),
    ):
        result = main(
            [
                "--issue",
                "42",
                "--summary",
                "Update docs",
                "--docs-only",
                "--dry-run",
            ]
        )
    assert result == 0


def test_main_submits_pr(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.submit_pr.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.submit_pr.git.current_branch", return_value="feature/x"),
        patch("standard_tooling.bin.submit_pr.git.read_output", return_value="feat: thing"),
        patch("standard_tooling.bin.submit_pr.git.run") as mock_git_run,
        patch(
            "standard_tooling.bin.submit_pr.github.create_pr",
            return_value="https://github.com/pr/1",
        ) as mock_create_pr,
        patch("standard_tooling.bin.submit_pr.github.auto_merge") as mock_auto_merge,
    ):
        result = main(["--issue", "42", "--summary", "Fix bug"])
    assert result == 0
    mock_git_run.assert_called_once_with("push", "-u", "origin", "feature/x")
    mock_create_pr.assert_called_once()
    mock_auto_merge.assert_called_once_with("https://github.com/pr/1", strategy="--squash")


def test_main_submits_pr_with_notes(tmp_path: Path) -> None:
    with (
        patch("standard_tooling.bin.submit_pr.git.repo_root", return_value=tmp_path),
        patch("standard_tooling.bin.submit_pr.git.current_branch", return_value="feature/x"),
        patch("standard_tooling.bin.submit_pr.git.read_output", return_value="feat: thing"),
        patch("standard_tooling.bin.submit_pr.git.run"),
        patch(
            "standard_tooling.bin.submit_pr.github.create_pr",
            return_value="https://github.com/pr/1",
        ),
        patch("standard_tooling.bin.submit_pr.github.auto_merge"),
    ):
        result = main(
            [
                "--issue",
                "42",
                "--summary",
                "Fix bug",
                "--notes",
                "Tested on macOS",
            ]
        )
    assert result == 0
