"""Tests for standard_tooling.bin.pr_issue_linkage."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.pr_issue_linkage import main

if TYPE_CHECKING:
    from pathlib import Path


def _write_event(tmp_path: Path, body: str) -> str:
    event = {"pull_request": {"body": body}}
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event))
    return str(event_file)


def test_missing_env_var() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert main() == 2


def test_missing_event_file() -> None:
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": "/nonexistent/event.json"}):
        assert main() == 2


def test_empty_body(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 1


def test_null_body(tmp_path: Path) -> None:
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps({"pull_request": {"body": None}}))
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": str(event_file)}):
        assert main() == 1


def test_no_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "This PR does something nice.")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 1


def test_fixes_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "## Summary\n\nFixes #42\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_closes_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "Closes #99\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_resolves_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "Resolves #7\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_ref_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "Ref #123\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_cross_repo_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "Fixes owner/repo#123\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_bullet_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "- Fixes #42\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_star_bullet_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "* Fixes #42\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_linkage_with_colon(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "Fixes: #42\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_indented_linkage(tmp_path: Path) -> None:
    event_path = _write_event(tmp_path, "  Fixes #42\n")
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": event_path}):
        assert main() == 0


def test_no_pull_request_key(tmp_path: Path) -> None:
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps({}))
    with patch.dict("os.environ", {"GITHUB_EVENT_PATH": str(event_file)}):
        assert main() == 1
