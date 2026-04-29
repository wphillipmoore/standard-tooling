"""Release-workflow branch identification."""

from __future__ import annotations


def is_release_branch(branch: str) -> bool:
    """Return True if the branch is part of the release workflow.

    All release-cycle branches use the ``release/`` prefix.
    """
    return branch.startswith("release/")
