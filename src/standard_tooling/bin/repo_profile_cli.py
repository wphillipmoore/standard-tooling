"""Validate the repository profile in ``docs/repository-standards.md``.

Checks that all required attributes are present and none contain
placeholder values.
"""

from __future__ import annotations

import sys
from dataclasses import fields

from standard_tooling.lib.repo_profile import PROFILE_FILENAME, read_profile


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    try:
        profile = read_profile()
    except FileNotFoundError:
        print(
            f"ERROR: repository profile file not found at {PROFILE_FILENAME}",
            file=sys.stderr,
        )
        return 2

    failed = 0
    for field in fields(profile):
        value = getattr(profile, field.name)
        if not value:
            print(
                f"ERROR: repository profile missing required attribute "
                f"'{field.name}' in {PROFILE_FILENAME}",
                file=sys.stderr,
            )
            failed = 1
            continue

        if "<" in value or ">" in value or "|" in value:
            print(
                f"ERROR: repository profile attribute '{field.name}' "
                f"appears to be a placeholder: {value}",
                file=sys.stderr,
            )
            failed = 1

    return failed


if __name__ == "__main__":
    sys.exit(main())
