"""Ensure a label exists in a GitHub repository. Creates it if missing.

Idempotent: exits 0 whether the label already existed or was created.
"""

from __future__ import annotations

import argparse
import sys

from standard_tooling.lib import github


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Ensure a GitHub label exists.")
    parser.add_argument("--repo", required=True, help="Repository (OWNER/REPO)")
    parser.add_argument("--label", required=True, help="Label name")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    existing = github.read_output(
        "label",
        "list",
        "--repo",
        args.repo,
        "--search",
        args.label,
        "--json",
        "name",
        "--jq",
        ".[].name",
    )
    if args.label in existing.splitlines():
        print(f"Label '{args.label}' already exists in {args.repo}")
    else:
        github.run("label", "create", args.label, "--repo", args.repo)
        print(f"Label '{args.label}' created in {args.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
