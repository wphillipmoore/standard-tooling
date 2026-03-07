"""Shared checks run for all repos — containerised via docker-test.

Sets ``DOCKER_DEV_IMAGE``, ``DOCKER_EXTRA_VOLUMES``, and
``DOCKER_TEST_CMD`` then delegates to ``docker_test.main()``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from standard_tooling.bin import docker_test


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    st_bin = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "bin")

    if not os.environ.get("DOCKER_DEV_IMAGE"):
        os.environ["DOCKER_DEV_IMAGE"] = "dev-python:3.14"
    os.environ["DOCKER_EXTRA_VOLUMES"] = f"{st_bin}:/st-bin:ro"
    os.environ["DOCKER_TEST_CMD"] = "export PATH=/st-bin:$PATH && validate-local-common-container"

    return docker_test.main()


if __name__ == "__main__":
    sys.exit(main())
