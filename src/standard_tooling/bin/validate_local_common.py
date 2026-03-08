"""Shared checks run for all repos — containerised via docker-test.

Sets ``DOCKER_DEV_IMAGE`` and ``DOCKER_TEST_CMD`` then delegates to
``docker_test.main()``.
"""

from __future__ import annotations

import os
import sys

from standard_tooling.bin import docker_test


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    if not os.environ.get("DOCKER_DEV_IMAGE"):
        os.environ["DOCKER_DEV_IMAGE"] = "dev-python:3.14"
    os.environ["DOCKER_TEST_CMD"] = "st-validate-local-common-container"

    return docker_test.main()


if __name__ == "__main__":
    sys.exit(main())
