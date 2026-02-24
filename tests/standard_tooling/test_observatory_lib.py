"""Tests for standard_tooling.lib.observatory."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import patch

from standard_tooling.lib.observatory import (
    CIStatus,
    RepoHealth,
    _collect_branches,
    _collect_ci,
    _collect_language,
    _collect_open_issues,
    _collect_open_prs,
    _collect_release,
    _format_date,
    _run_gh,
    collect_repo_health,
    list_project_repos,
    project_title,
    render_report,
)
from standard_tooling.lib.registry import RegistryVersion

# ---------------------------------------------------------------------------
# list_project_repos
# ---------------------------------------------------------------------------


def test_list_project_repos() -> None:
    with patch(
        "standard_tooling.lib.observatory.github.read_output",
        return_value="acme/repo-b\nacme/repo-a\nacme/repo-a\n",
    ):
        repos = list_project_repos("acme", "5")
    assert repos == ["acme/repo-a", "acme/repo-b"]


def test_list_project_repos_empty() -> None:
    with patch(
        "standard_tooling.lib.observatory.github.read_output",
        return_value="",
    ):
        assert list_project_repos("acme", "5") == []


# ---------------------------------------------------------------------------
# project_title
# ---------------------------------------------------------------------------


def test_project_title() -> None:
    with patch(
        "standard_tooling.lib.observatory.github.read_output",
        return_value="My Project",
    ):
        assert project_title("acme", "5") == "My Project"


# ---------------------------------------------------------------------------
# collect_repo_health
# ---------------------------------------------------------------------------


def _gh_side_effect(*args: str) -> str:
    """Simulate gh CLI responses based on arguments."""
    joined = " ".join(args)
    if "primaryLanguage" in joined:
        return "Python"
    if "/branches" in joined:
        return "main\ndevelop\nfeature/wip\n"
    if "run list" in joined:
        return json.dumps([{"conclusion": "success", "status": "completed"}])
    if "issue list" in joined:
        return "3"
    if "pr list" in joined:
        return "1"
    if "release list" in joined:
        return json.dumps([{"tagName": "v1.0.0", "publishedAt": "2025-01-15T10:00:00Z"}])
    return ""


def test_collect_repo_health() -> None:
    with (
        patch("standard_tooling.lib.observatory.registry.lookup", return_value=None),
        patch("standard_tooling.lib.observatory._run_gh", side_effect=_gh_side_effect),
        patch("standard_tooling.lib.observatory._collect_language", return_value="Python"),
    ):
        health = collect_repo_health("acme/repo")

    assert health.name == "acme/repo"
    assert health.error == ""


def _completed(returncode: int = 0, stdout: str = "") -> object:
    """Build a fake CompletedProcess."""
    import subprocess

    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout)


def test_collect_repo_health_with_error() -> None:
    with patch(
        "standard_tooling.lib.observatory._collect_language",
        side_effect=RuntimeError("boom"),
    ):
        health = collect_repo_health("acme/broken")
    assert health.name == "acme/broken"
    assert "boom" in health.error


# ---------------------------------------------------------------------------
# render_report
# ---------------------------------------------------------------------------

_FIXED_TS = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)


def test_render_report_basic() -> None:
    repos = [
        RepoHealth(
            name="acme/repo-a",
            open_issues=2,
            open_prs=1,
            latest_release="v1.0.0",
            release_date="2025-01-15T10:00:00Z",
            primary_language="Python",
            ci_statuses=[CIStatus(branch="main", conclusion="success", status="completed")],
        ),
    ]
    report = render_report(repos, "Test Report", timestamp=_FIXED_TS)

    assert "# Test Report" in report
    assert "2025-06-15 12:00 UTC" in report
    assert "| Repositories | 1 |" in report
    assert "| CI failures | 0 |" in report
    assert "acme/repo-a" in report
    assert "v1.0.0" in report


def test_render_report_with_alerts() -> None:
    repos = [
        RepoHealth(
            name="acme/failing",
            ci_statuses=[CIStatus(branch="main", conclusion="failure", status="completed")],
            wip_branches=["feature/old"],
            latest_release="v1.0.0",
            registry_version=RegistryVersion(name="failing", version="0.9.0", registry="PyPI"),
        ),
    ]
    report = render_report(repos, "Alert Report", timestamp=_FIXED_TS)

    assert "## Alerts" in report
    assert "**CI failure**" in report
    assert "**Version drift**" in report
    assert "**WIP branches**" in report


def test_render_report_error_repo() -> None:
    repos = [
        RepoHealth(name="acme/broken", error="data unavailable"),
    ]
    report = render_report(repos, "Error Report", timestamp=_FIXED_TS)
    assert "**Data collection error**" in report
    assert "data unavailable" in report


def test_render_report_no_alerts() -> None:
    repos = [
        RepoHealth(
            name="acme/clean",
            ci_statuses=[CIStatus(branch="main", conclusion="success", status="completed")],
        ),
    ]
    report = render_report(repos, "Clean Report", timestamp=_FIXED_TS)
    assert "## Alerts" not in report


def test_render_report_registry_version() -> None:
    repos = [
        RepoHealth(
            name="acme/lib",
            primary_language="Python",
            latest_release="v2.0.0",
            registry_version=RegistryVersion(name="lib", version="2.0.0", registry="PyPI"),
        ),
    ]
    report = render_report(repos, "Registry Report", timestamp=_FIXED_TS)
    assert "PyPI version" in report
    assert "2.0.0" in report
    # No drift alert since versions match
    assert "## Alerts" not in report


# ---------------------------------------------------------------------------
# _run_gh
# ---------------------------------------------------------------------------


def test_run_gh_success() -> None:
    with patch("standard_tooling.lib.observatory.subprocess.run") as mock_run:
        mock_run.return_value = _completed(stdout="hello\n")
        assert _run_gh("repo", "view") == "hello"


def test_run_gh_failure() -> None:
    import subprocess as sp

    with patch(
        "standard_tooling.lib.observatory.subprocess.run",
        side_effect=sp.CalledProcessError(1, "gh"),
    ):
        assert _run_gh("bad", "cmd") == ""


# ---------------------------------------------------------------------------
# _collect_* helpers
# ---------------------------------------------------------------------------


def test_collect_branches() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value="main\ndevelop\nfeat/x\n"):
        result = _collect_branches("acme/repo")
    assert result == ["feat/x"]


def test_collect_ci_with_runs() -> None:
    runs_json = json.dumps([{"conclusion": "success", "status": "completed"}])
    with patch("standard_tooling.lib.observatory._run_gh", return_value=runs_json):
        statuses = _collect_ci("acme/repo")
    # Both main and develop get the same mock response
    assert len(statuses) == 2
    assert statuses[0].branch == "main"
    assert statuses[0].conclusion == "success"


def test_collect_ci_no_runs() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value=""):
        statuses = _collect_ci("acme/repo")
    assert statuses == []


def test_collect_ci_empty_json_list() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value="[]"):
        statuses = _collect_ci("acme/repo")
    assert statuses == []


def test_collect_open_issues() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value="5"):
        assert _collect_open_issues("acme/repo") == 5


def test_collect_open_issues_empty() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value=""):
        assert _collect_open_issues("acme/repo") == 0


def test_collect_open_prs() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value="2"):
        assert _collect_open_prs("acme/repo") == 2


def test_collect_release_with_data() -> None:
    data = json.dumps([{"tagName": "v1.0.0", "publishedAt": "2025-06-01T00:00:00Z"}])
    with patch("standard_tooling.lib.observatory._run_gh", return_value=data):
        tag, date = _collect_release("acme/repo")
    assert tag == "v1.0.0"
    assert date == "2025-06-01T00:00:00Z"


def test_collect_release_empty() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value=""):
        tag, date = _collect_release("acme/repo")
    assert tag == ""
    assert date == ""


def test_collect_release_empty_list() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value="[]"):
        tag, date = _collect_release("acme/repo")
    assert tag == ""
    assert date == ""


def test_collect_language() -> None:
    with patch("standard_tooling.lib.observatory._run_gh", return_value="Python"):
        assert _collect_language("acme/repo") == "Python"


# ---------------------------------------------------------------------------
# _format_date
# ---------------------------------------------------------------------------


def test_format_date_iso() -> None:
    assert _format_date("2025-01-15T10:00:00Z") == "2025-01-15"


def test_format_date_empty() -> None:
    assert _format_date("") == ""


def test_format_date_invalid() -> None:
    assert _format_date("not-a-date") == "not-a-date"


# ---------------------------------------------------------------------------
# render_report default timestamp
# ---------------------------------------------------------------------------


def test_render_report_default_timestamp() -> None:
    repos = [RepoHealth(name="acme/repo")]
    report = render_report(repos, "Default TS Report")
    assert "# Default TS Report" in report
    assert "Generated:" in report


# ---------------------------------------------------------------------------
# collect_repo_health with registry lookup
# ---------------------------------------------------------------------------


def test_collect_repo_health_with_registry() -> None:
    rv = RegistryVersion(name="repo", version="1.0.0", registry="PyPI")
    with (
        patch("standard_tooling.lib.observatory._run_gh", side_effect=_gh_side_effect),
        patch("standard_tooling.lib.observatory._collect_language", return_value="Python"),
        patch("standard_tooling.lib.observatory.registry.lookup", return_value=rv),
    ):
        health = collect_repo_health("acme/repo")
    assert health.registry_version == rv
    assert health.primary_language == "Python"


def test_collect_repo_health_no_language() -> None:
    with (
        patch("standard_tooling.lib.observatory._run_gh", return_value=""),
        patch("standard_tooling.lib.observatory._collect_language", return_value=""),
        patch("standard_tooling.lib.observatory.registry.lookup") as mock_lookup,
    ):
        health = collect_repo_health("acme/repo")
    mock_lookup.assert_not_called()
    assert health.registry_version is None
