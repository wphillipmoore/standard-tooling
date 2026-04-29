"""Block until a PR's required checks pass.

Thin wrapper around ``gh pr checks --watch --fail-fast`` so agents have a
single command instead of inlining gh flags. Surfaces any check failure
with a non-zero exit code.
"""

from __future__ import annotations

import argparse
import sys

from standard_tooling.lib import github


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Block until a PR's required checks pass.",
    )
    parser.add_argument("pr", help="PR URL or number")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"Waiting for checks to pass on {args.pr}...")
    github.wait_for_checks(args.pr)
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
