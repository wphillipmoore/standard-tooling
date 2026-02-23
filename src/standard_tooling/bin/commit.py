"""Commit wrapper that constructs standards-compliant commit messages.

Resolves Co-Authored-By identities from docs/repository-standards.md.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from standard_tooling.lib import git, repo_profile

ALLOWED_TYPES = ("feat", "fix", "docs", "style", "refactor", "test", "chore", "ci", "build")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Construct a standards-compliant conventional commit."
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=ALLOWED_TYPES,
        dest="commit_type",
        help="Conventional commit type",
    )
    parser.add_argument("--scope", default="", help="Conventional commit scope")
    parser.add_argument("--message", required=True, help="Commit description")
    parser.add_argument("--body", default="", help="Detailed commit body")
    parser.add_argument("--agent", required=True, help="AI tool identity (e.g. claude, codex)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = git.repo_root()

    identity = repo_profile.resolve_co_author(args.agent, root)

    if not git.has_staged_changes():
        print(
            "ERROR: no staged changes. Stage files with 'git add' before committing.",
            file=sys.stderr,
        )
        return 1

    subject = args.commit_type
    if args.scope:
        subject = f"{subject}({args.scope})"
    subject = f"{subject}: {args.message}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(f"{subject}\n")
        if args.body:
            f.write(f"\n{args.body}\n")
        f.write(f"\n{identity}\n")
        tmp_path = f.name

    try:
        git.run("commit", "--file", tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
