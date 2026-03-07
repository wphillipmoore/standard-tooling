"""Pre-commit hook enforcing branch naming conventions.

Blocks detached HEAD, direct commits to protected branches, and
validates branch names against the repository's branching model.
"""

from __future__ import annotations

import re
import sys

from standard_tooling.lib import git, repo_profile

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


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    current_branch = git.current_branch()

    if current_branch == "HEAD":
        print("ERROR: detached HEAD is not allowed for commits.", file=sys.stderr)
        print("Create a short-lived branch and open a PR.", file=sys.stderr)
        return 1

    if current_branch in _PROTECTED_BRANCHES:
        print(
            f"ERROR: direct commits to protected branches are forbidden ({current_branch}).",
            file=sys.stderr,
        )
        print("Create a short-lived branch and open a PR.", file=sys.stderr)
        return 1

    root = git.repo_root()
    branching_model = ""
    try:
        profile = repo_profile.read_profile(root)
        branching_model = profile.branching_model
    except FileNotFoundError:
        pass

    if branching_model and branching_model not in _BRANCHING_MODELS:
        profile_file = root / repo_profile.PROFILE_FILENAME
        print(
            f"ERROR: unrecognized branching_model '{branching_model}' in {profile_file}.",
            file=sys.stderr,
        )
        return 1

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

    if not re.search(allowed_regex, current_branch):
        print(
            f"ERROR: branch name must use {allowed_display} ({current_branch}).",
            file=sys.stderr,
        )
        print("Rename the branch before committing.", file=sys.stderr)
        return 1

    if _ISSUE_REQUIRED_RE.search(current_branch) and not _ISSUE_FORMAT_RE.match(current_branch):
        print(
            f"ERROR: branch name must include a repo issue number ({current_branch}).",
            file=sys.stderr,
        )
        print("Expected format: {type}/{issue}-{description}", file=sys.stderr)
        print("Example: feature/42-add-caching", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
