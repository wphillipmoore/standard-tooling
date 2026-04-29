"""Release-workflow branch identification."""

from __future__ import annotations

import fnmatch

_RELEASE_BRANCH_PATTERNS = ("release/*", "chore/bump-version-*")


def is_release_branch(branch: str) -> bool:
    """Return True if the branch matches a release-workflow pattern."""
    return any(fnmatch.fnmatch(branch, p) for p in _RELEASE_BRANCH_PATTERNS)
