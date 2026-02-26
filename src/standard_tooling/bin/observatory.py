"""Generate Markdown health reports for repositories in a GitHub Project."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from standard_tooling.lib.observatory import (
    collect_repo_health,
    list_project_repos,
    project_title,
    render_report,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a health report for repos in a GitHub Project.",
    )
    parser.add_argument("--owner", required=True, help="GitHub owner")
    parser.add_argument("--project", required=True, help="Project number")
    parser.add_argument(
        "--output-dir",
        help="Directory to write the report file (default: stdout)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    title = project_title(args.owner, args.project)
    if not title:
        title = f"Project {args.project}"
    title = f"Observatory: {title}"

    repos = list_project_repos(args.owner, args.project)
    if not repos:
        print(f"No repositories found for project {args.project}.", file=sys.stderr)
        return 1

    print(f"Collecting health data for {len(repos)} repositories...", file=sys.stderr)

    health_data = []
    for repo in repos:
        print(f"  {repo}...", file=sys.stderr)
        health_data.append(collect_repo_health(repo))

    now = datetime.now(tz=UTC)
    report = render_report(health_data, title, timestamp=now)

    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"observatory-{now.strftime('%Y-%m-%dT%H-%M-%S')}.md"
        out_path = out_dir / filename
        out_path.write_text(report)
        print(f"Report written to {out_path}", file=sys.stderr)
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
