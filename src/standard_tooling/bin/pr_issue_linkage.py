"""Check that a pull request body includes primary issue linkage.

Reads the GitHub event payload from ``GITHUB_EVENT_PATH`` and validates
that the PR body contains a linkage keyword (Fixes, Closes, Resolves,
or Ref) followed by an issue reference.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_LINKAGE_RE = re.compile(
    r"^\s*[-*]?\s*(Fixes|Closes|Resolves|Ref):?\s+"
    r"([a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)?#[0-9]+",
    re.MULTILINE,
)


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")

    if not event_path:
        print("ERROR: GITHUB_EVENT_PATH is not set.", file=sys.stderr)
        return 2

    event_file = Path(event_path)
    if not event_file.is_file():
        print(f"ERROR: event payload not found at {event_path}", file=sys.stderr)
        return 2

    with event_file.open(encoding="utf-8") as f:
        event = json.load(f)

    pr_body: str = event.get("pull_request", {}).get("body", "") or ""

    if not pr_body:
        print(
            "ERROR: pull request body is empty; issue linkage is required.",
            file=sys.stderr,
        )
        return 1

    if not _LINKAGE_RE.search(pr_body):
        print(
            "ERROR: pull request body must include primary issue linkage "
            "(Fixes #123, Closes #123, Resolves #123, or Ref #123). "
            "Cross-repo references (owner/repo#123) are also accepted.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
