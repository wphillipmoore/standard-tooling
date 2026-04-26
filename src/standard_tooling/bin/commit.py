"""Commit wrapper that constructs standards-compliant commit messages.

Resolves Co-Authored-By identities from docs/repository-standards.md.
Performs branch / context validation (formerly in
`standard_tooling.bin.pre_commit_hook`, removed under the host-level-tool
spec — see docs/specs/host-level-tool.md). Sets ST_COMMIT_CONTEXT=1
before invoking `git commit` so the `.githooks/pre-commit` env-var gate
admits the resulting commit.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

from standard_tooling.lib import git, repo_profile

ALLOWED_TYPES = ("feat", "fix", "docs", "style", "refactor", "test", "chore", "ci", "build")

_PROTECTED_BRANCHES = {"develop", "release", "main"}

_BRANCHING_MODELS: dict[str, tuple[str, str]] = {
    "docs-single-branch": (
        r"^(feature|bugfix|chore)/",
        "feature/*, bugfix/*, or chore/*",
    ),
    "application-promotion": (
        r"^(feature|bugfix|hotfix|chore|promotion)/",
        "feature/*, bugfix/*, hotfix/*, chore/*, or promotion/*",
    ),
    "library-release": (
        r"^(feature|bugfix|hotfix|chore|release)/",
        "feature/*, bugfix/*, hotfix/*, chore/*, or release/*",
    ),
}

_ISSUE_REQUIRED_RE = re.compile(r"^(feature|bugfix|hotfix|chore)/")
_ISSUE_FORMAT_RE = re.compile(r"^(feature|bugfix|hotfix|chore)/[0-9]+-[a-z0-9][a-z0-9.-]*$")
_WORKTREE_SCOPED_RE = re.compile(r"^(feature|bugfix|hotfix|chore)/")
_WORKTREES_DIRNAME = ".worktrees"

# Env-var contract with `.githooks/pre-commit`. The gate admits any
# `git commit` that runs with this variable set to "1"; st-commit sets
# it just before invoking git commit. See docs/specs/host-level-tool.md
# "Git hooks" section.
_GATE_ENV_VAR = "ST_COMMIT_CONTEXT"
_GATE_ENABLED_VALUE = "1"


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


def _reject(reason: str, *hints: str) -> int:
    """Print rejection reason and hints to stderr; return 1."""
    print(reason, file=sys.stderr)
    for hint in hints:
        print(hint, file=sys.stderr)
    return 1


def _validate_commit_context() -> int:
    """Run the five branch / context checks before any commit.

    Mirrors the pre-host-level-tool `pre_commit_hook.py` logic exactly.
    Returns 0 on success, 1 on rejection (with diagnostic on stderr).
    """
    current_branch = git.current_branch()

    # Check 1: detached HEAD
    if current_branch == "HEAD":
        return _reject(
            "ERROR: detached HEAD is not allowed for commits.",
            "Create a short-lived branch and open a PR.",
        )

    # Check 2: protected branches
    if current_branch in _PROTECTED_BRANCHES:
        return _reject(
            f"ERROR: direct commits to protected branches are forbidden ({current_branch}).",
            "Create a short-lived branch and open a PR.",
        )

    root = git.repo_root()
    branching_model = ""
    try:
        profile = repo_profile.read_profile(root)
        branching_model = profile.branching_model
    except FileNotFoundError:
        pass

    if branching_model and branching_model not in _BRANCHING_MODELS:
        profile_file = root / repo_profile.PROFILE_FILENAME
        return _reject(
            f"ERROR: unrecognized branching_model '{branching_model}' in {profile_file}.",
        )

    if branching_model:
        allowed_regex, allowed_display = _BRANCHING_MODELS[branching_model]
    else:
        profile_file = root / repo_profile.PROFILE_FILENAME
        print(
            f"WARNING: branching_model not found in {profile_file}; "
            "falling back to feature/*/bugfix/*.",
            file=sys.stderr,
        )
        allowed_regex = r"^(feature|bugfix|chore)/"
        allowed_display = "feature/*, bugfix/*, or chore/*"

    # Check 3: branch prefix matches branching model
    if not re.search(allowed_regex, current_branch):
        return _reject(
            f"ERROR: branch name must use {allowed_display} ({current_branch}).",
            "Rename the branch before committing.",
        )

    # Check 4: feature/bugfix/hotfix/chore branches must include an issue number
    if _ISSUE_REQUIRED_RE.search(current_branch) and not _ISSUE_FORMAT_RE.match(current_branch):
        return _reject(
            f"ERROR: branch name must include a repo issue number ({current_branch}).",
            "Expected format: {type}/{issue}-{description}",
            "Example: feature/42-add-caching",
        )

    # Check 5: feature-branch commits from the main worktree are forbidden
    # when `.worktrees/` is present (worktree-convention rule 3).
    if (
        _WORKTREE_SCOPED_RE.search(current_branch)
        and (root / _WORKTREES_DIRNAME).is_dir()
        and git.is_main_worktree()
    ):
        return _reject(
            "ERROR: feature-branch commits from the main worktree are forbidden "
            f"({current_branch}).",
            "The main worktree is read-only under the worktree convention; "
            "edits flow through a worktree on a feature branch.",
            "To proceed:",
            f"  cd {root}/{_WORKTREES_DIRNAME}/<issue-N-slug>  "
            "# if a worktree already exists for this branch",
            f"  git worktree add {_WORKTREES_DIRNAME}/issue-N-<slug> "
            f"-b {current_branch} origin/develop  # to create one",
            "See docs/specs/worktree-convention.md for the full convention.",
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    rc = _validate_commit_context()
    if rc != 0:
        return rc

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
        # Set the env-var gate signal so `.githooks/pre-commit` admits the
        # resulting `git commit`. See docs/specs/host-level-tool.md.
        os.environ[_GATE_ENV_VAR] = _GATE_ENABLED_VALUE
        git.run("commit", "--file", tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
