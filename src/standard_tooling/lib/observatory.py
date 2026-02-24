"""Observatory: repo health collection and Markdown report rendering."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime

from standard_tooling.lib import github, registry

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class CIStatus:
    """CI run result for a single branch."""

    branch: str
    conclusion: str  # "success", "failure", "cancelled", etc.
    status: str  # "completed", "in_progress", etc.


@dataclass
class RepoHealth:
    """Health snapshot for a single repository."""

    name: str
    open_issues: int = 0
    open_prs: int = 0
    latest_release: str = ""
    release_date: str = ""
    primary_language: str = ""
    wip_branches: list[str] = field(default_factory=list)
    ci_statuses: list[CIStatus] = field(default_factory=list)
    registry_version: registry.RegistryVersion | None = None
    error: str = ""


# ---------------------------------------------------------------------------
# Repo discovery (mirrors list_project_repos.py pattern)
# ---------------------------------------------------------------------------

_ETERNAL_BRANCHES = frozenset({"main", "master", "develop", "gh-pages"})


def list_project_repos(owner: str, project: str) -> list[str]:
    """Return sorted, unique repos linked to a GitHub Project."""
    jq_filter = (
        f".[] | select(.projectsV2.Nodes | length > 0) "
        f"| select(.projectsV2.Nodes[].number == {project}) "
        f"| .nameWithOwner"
    )
    output = github.read_output(
        "repo",
        "list",
        owner,
        "--json",
        "nameWithOwner,projectsV2",
        "--limit",
        "100",
        "--jq",
        jq_filter,
    )
    return sorted({r for r in output.splitlines() if r})


def project_title(owner: str, project: str) -> str:
    """Return the human-readable title of a GitHub Project."""
    return github.read_output(
        "project",
        "view",
        project,
        "--owner",
        owner,
        "--format",
        "json",
        "--jq",
        ".title",
    )


# ---------------------------------------------------------------------------
# Per-repo data collection
# ---------------------------------------------------------------------------


def _run_gh(*args: str) -> str:
    """Run a ``gh`` command, returning stripped stdout or empty on failure."""
    try:
        result = subprocess.run(  # noqa: S603, S607
            ("gh", *args),
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def _collect_branches(repo: str) -> list[str]:
    raw = _run_gh(
        "api",
        f"repos/{repo}/branches",
        "--paginate",
        "--jq",
        ".[].name",
    )
    return [b for b in raw.splitlines() if b and b not in _ETERNAL_BRANCHES]


def _collect_ci(repo: str) -> list[CIStatus]:
    statuses: list[CIStatus] = []
    eternal = ["main", "develop"]
    for branch in eternal:
        raw = _run_gh(
            "run",
            "list",
            "--repo",
            repo,
            "--branch",
            branch,
            "--limit",
            "1",
            "--json",
            "conclusion,status",
        )
        if not raw:
            continue
        runs = json.loads(raw)
        if runs:
            statuses.append(
                CIStatus(
                    branch=branch,
                    conclusion=runs[0].get("conclusion", ""),
                    status=runs[0].get("status", ""),
                )
            )
    return statuses


def _collect_open_issues(repo: str) -> int:
    raw = _run_gh(
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--json",
        "number",
        "--jq",
        "length",
    )
    return int(raw) if raw else 0


def _collect_open_prs(repo: str) -> int:
    raw = _run_gh(
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--json",
        "number",
        "--jq",
        "length",
    )
    return int(raw) if raw else 0


def _collect_release(repo: str) -> tuple[str, str]:
    raw = _run_gh(
        "release",
        "list",
        "--repo",
        repo,
        "--limit",
        "1",
        "--json",
        "tagName,publishedAt",
    )
    if not raw:
        return "", ""
    releases = json.loads(raw)
    if not releases:
        return "", ""
    return releases[0].get("tagName", ""), releases[0].get("publishedAt", "")


def _collect_language(repo: str) -> str:
    return _run_gh(
        "repo",
        "view",
        repo,
        "--json",
        "primaryLanguage",
        "--jq",
        ".primaryLanguage.name",
    )


def collect_repo_health(repo: str) -> RepoHealth:
    """Collect all health data for a single repo. Never raises."""
    health = RepoHealth(name=repo)
    try:
        health.primary_language = _collect_language(repo)
        health.wip_branches = _collect_branches(repo)
        health.ci_statuses = _collect_ci(repo)
        health.open_issues = _collect_open_issues(repo)
        health.open_prs = _collect_open_prs(repo)
        health.latest_release, health.release_date = _collect_release(repo)

        if health.primary_language:
            owner, name = repo.split("/", 1)
            health.registry_version = registry.lookup(health.primary_language, owner, name)
    except Exception as exc:  # noqa: BLE001
        health.error = str(exc)
        print(f"Warning: error collecting data for {repo}: {exc}", file=sys.stderr)
    return health


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _format_date(iso_date: str) -> str:
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return iso_date


def render_report(
    repos: list[RepoHealth],
    title: str,
    timestamp: datetime | None = None,
) -> str:
    """Render a Markdown health report."""
    if timestamp is None:
        timestamp = datetime.now(tz=UTC)

    lines: list[str] = []
    ts_str = timestamp.strftime("%Y-%m-%d %H:%M UTC")

    # Title
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Generated: {ts_str}")
    lines.append("")

    # Summary
    ci_failures = sum(1 for r in repos for s in r.ci_statuses if s.conclusion == "failure")
    stale_count = sum(len(r.wip_branches) for r in repos)
    drift_count = sum(
        1
        for r in repos
        if r.registry_version
        and r.latest_release
        and r.registry_version.version != r.latest_release.lstrip("v")
    )

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Repositories | {len(repos)} |")
    lines.append(f"| CI failures | {ci_failures} |")
    lines.append(f"| WIP branches | {stale_count} |")
    lines.append(f"| Version drift | {drift_count} |")
    lines.append("")

    # Alerts
    alerts: list[str] = []
    for r in repos:
        for s in r.ci_statuses:
            if s.conclusion == "failure":
                alerts.append(f"- **CI failure**: {r.name} on `{s.branch}`")
        if r.registry_version and r.latest_release:
            reg_ver = r.registry_version.version
            rel_ver = r.latest_release.lstrip("v")
            if reg_ver != rel_ver:
                alerts.append(
                    f"- **Version drift**: {r.name} — "
                    f"release `{r.latest_release}`, "
                    f"{r.registry_version.registry} `{r.registry_version.version}`"
                )
        if r.wip_branches:
            alerts.append(
                f"- **WIP branches**: {r.name} — " + ", ".join(f"`{b}`" for b in r.wip_branches)
            )

    if alerts:
        lines.append("## Alerts")
        lines.append("")
        lines.extend(alerts)
        lines.append("")

    # Per-repo details
    for r in repos:
        lines.append(f"## {r.name}")
        lines.append("")

        if r.error:
            lines.append(f"**Data collection error**: {r.error}")
            lines.append("")
            continue

        # Issues / PRs / Release
        lines.append("| Stat | Value |")
        lines.append("| --- | --- |")
        lines.append(f"| Language | {r.primary_language or 'unknown'} |")
        lines.append(f"| Open issues | {r.open_issues} |")
        lines.append(f"| Open PRs | {r.open_prs} |")
        release_str = r.latest_release or "none"
        if r.release_date:
            release_str += f" ({_format_date(r.release_date)})"
        lines.append(f"| Latest release | {release_str} |")
        if r.registry_version:
            lines.append(
                f"| {r.registry_version.registry} version | {r.registry_version.version} |"
            )
        lines.append("")

        # CI status
        if r.ci_statuses:
            lines.append("### CI Status")
            lines.append("")
            lines.append("| Branch | Status | Conclusion |")
            lines.append("| --- | --- | --- |")
            for s in r.ci_statuses:
                lines.append(f"| {s.branch} | {s.status} | {s.conclusion} |")
            lines.append("")

        # WIP branches
        if r.wip_branches:
            lines.append("### WIP Branches")
            lines.append("")
            for b in r.wip_branches:
                lines.append(f"- `{b}`")
            lines.append("")

    return "\n".join(lines)
