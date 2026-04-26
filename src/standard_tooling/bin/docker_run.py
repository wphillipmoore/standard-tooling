"""Run an arbitrary command inside a dev container.

Auto-detects the project language to select a default Docker image.
Falls back to dev-base:latest when no language is detected and
DOCKER_DEV_IMAGE is not set.  The command to run is taken from CLI
arguments after ``--``.
"""

from __future__ import annotations

import os
import sys

from standard_tooling.lib import git
from standard_tooling.lib.docker import (
    assert_docker_available,
    build_docker_args,
    default_image,
    detect_language,
)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    # Split on -- separator
    if "--" in args:
        idx = args.index("--")
        command = args[idx + 1 :]
    else:
        command = args

    if not command:
        print("Usage: st-docker-run [--] <command> [args...]", file=sys.stderr)
        return 1

    if not os.environ.get("GH_TOKEN"):
        print(
            "ERROR: GH_TOKEN is not set. Set GH_TOKEN in your environment before\n"
            "running st-docker-run. See docs/development/environment-setup.md.",
            file=sys.stderr,
        )
        return 1

    repo_root = git.repo_root()
    lang = detect_language(repo_root)
    image = os.environ.get("DOCKER_DEV_IMAGE") or default_image(lang, fallback=True)

    print(f"Language: {lang or '<none>'}")
    print(f"Image:    {image}")
    print(f"Command:  {' '.join(command)}")
    network = os.environ.get("DOCKER_NETWORK", "")
    if network:
        print(f"Network:  {network}")
    print("---")

    assert_docker_available()

    docker_args = build_docker_args(repo_root, image, command)
    os.execvp("docker", docker_args)  # noqa: S606, S607
    return 0  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
