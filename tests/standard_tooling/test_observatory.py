"""Tests for standard_tooling.bin.observatory."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.observatory import main, parse_args
from standard_tooling.lib.observatory import RepoHealth

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_args_required() -> None:
    args = parse_args(["--owner", "acme", "--project", "5"])
    assert args.owner == "acme"
    assert args.project == "5"
    assert args.output_dir is None


def test_parse_args_output_dir() -> None:
    args = parse_args(["--owner", "acme", "--project", "5", "--output-dir", "./out"])
    assert args.output_dir == "./out"


def test_main_no_repos() -> None:
    with (
        patch(
            "standard_tooling.bin.observatory.project_title",
            return_value="Test Project",
        ),
        patch(
            "standard_tooling.bin.observatory.list_project_repos",
            return_value=[],
        ),
    ):
        result = main(["--owner", "acme", "--project", "5"])
    assert result == 1


def test_main_stdout(capsys: object) -> None:
    health = RepoHealth(name="acme/repo", open_issues=1, primary_language="Python")
    with (
        patch(
            "standard_tooling.bin.observatory.project_title",
            return_value="My Project",
        ),
        patch(
            "standard_tooling.bin.observatory.list_project_repos",
            return_value=["acme/repo"],
        ),
        patch(
            "standard_tooling.bin.observatory.collect_repo_health",
            return_value=health,
        ),
    ):
        result = main(["--owner", "acme", "--project", "5"])
    assert result == 0


def test_main_output_dir(tmp_path: Path) -> None:
    health = RepoHealth(name="acme/repo", open_issues=0)
    with (
        patch(
            "standard_tooling.bin.observatory.project_title",
            return_value="My Project",
        ),
        patch(
            "standard_tooling.bin.observatory.list_project_repos",
            return_value=["acme/repo"],
        ),
        patch(
            "standard_tooling.bin.observatory.collect_repo_health",
            return_value=health,
        ),
    ):
        result = main(["--owner", "acme", "--project", "5", "--output-dir", str(tmp_path)])
    assert result == 0
    files = list(tmp_path.glob("observatory-*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "Observatory: My Project" in content


def test_main_fallback_title() -> None:
    health = RepoHealth(name="acme/repo")
    with (
        patch(
            "standard_tooling.bin.observatory.project_title",
            return_value="",
        ),
        patch(
            "standard_tooling.bin.observatory.list_project_repos",
            return_value=["acme/repo"],
        ),
        patch(
            "standard_tooling.bin.observatory.collect_repo_health",
            return_value=health,
        ),
    ):
        result = main(["--owner", "acme", "--project", "5"])
    assert result == 0
