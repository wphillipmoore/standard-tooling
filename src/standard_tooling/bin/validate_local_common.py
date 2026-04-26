"""Shared validation checks run for all repos.

Container-local: assumes the caller (`st-validate-local`) is itself running
inside a dev container via `st-docker-run`.  Delegates to the implementation
in ``validate_local_common_container`` — the same work the old version
dispatched to via ``st-docker-test``, now called directly.
"""

from __future__ import annotations

import sys

from standard_tooling.bin import validate_local_common_container


def main(argv: list[str] | None = None) -> int:
    return validate_local_common_container.main(argv)


if __name__ == "__main__":
    sys.exit(main())
