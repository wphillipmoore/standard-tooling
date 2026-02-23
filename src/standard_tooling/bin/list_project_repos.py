"""List unique repositories linked to a GitHub Project."""

from __future__ import annotations

import argparse
import sys

from standard_tooling.lib import github


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="List repos linked to a GitHub Project.")
    parser.add_argument("--owner", required=True, help="GitHub owner")
    parser.add_argument("--project", required=True, help="Project number")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    jq_filter = (
        f".[] | select(.projectsV2.Nodes | length > 0) "
        f"| select(.projectsV2.Nodes[].number == {args.project}) "
        f"| .nameWithOwner"
    )
    output = github.read_output(
        "repo", "list", args.owner,
        "--json", "nameWithOwner,projectsV2",
        "--limit", "100",
        "--jq", jq_filter,
    )
    for repo in sorted(set(output.splitlines())):
        if repo:
            print(repo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
