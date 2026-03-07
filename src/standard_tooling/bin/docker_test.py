"""Run a repository's test suite inside a dev container.

Auto-detects the project language from package manager files and selects
a default Docker image and test command.  All defaults can be overridden
via environment variables.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from standard_tooling.lib import git

if TYPE_CHECKING:
    from pathlib import Path

_DEFAULT_IMAGES: dict[str, str] = {
    "ruby": "dev-ruby:3.4",
    "python": "dev-python:3.14",
    "go": "dev-go:1.26",
    "rust": "dev-rust:1.93",
    "java": "dev-java:21",
}

_DEFAULT_COMMANDS: dict[str, str] = {
    "ruby": "bundle install --jobs 4 && bundle exec rake",
    "python": "uv sync && uv run pytest tests/ -v",
    "go": "go test ./...",
    "rust": "cargo test",
    "java": "./mvnw verify",
}


def _detect_language(repo_root: Path) -> str:
    """Detect the project language from repo contents."""
    if (repo_root / "Gemfile").is_file():
        return "ruby"
    if (repo_root / "pyproject.toml").is_file():
        return "python"
    if (repo_root / "go.mod").is_file():
        return "go"
    if (repo_root / "Cargo.toml").is_file():
        return "rust"
    if (repo_root / "pom.xml").is_file() or (repo_root / "mvnw").is_file():
        return "java"
    return ""


def build_docker_args(repo_root: Path, lang: str) -> list[str]:
    """Build the docker run argument list."""
    image = os.environ.get("DOCKER_DEV_IMAGE") or _DEFAULT_IMAGES.get(lang, "")
    test_cmd = os.environ.get("DOCKER_TEST_CMD") or _DEFAULT_COMMANDS.get(lang, "")
    network = os.environ.get("DOCKER_NETWORK", "")

    if not image:
        print(f"ERROR: no Docker image configured for language: {lang}", file=sys.stderr)
        sys.exit(1)

    if not test_cmd:
        print(f"ERROR: no test command configured for language: {lang}", file=sys.stderr)
        sys.exit(1)

    docker_args = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{repo_root}:/workspace",
        "-w",
        "/workspace",
    ]

    if network:
        docker_args.extend(["--network", network])

    extra_volumes = os.environ.get("DOCKER_EXTRA_VOLUMES", "")
    if extra_volumes:
        for vol in extra_volumes.split(";"):
            vol = vol.strip()
            if vol:
                docker_args.extend(["-v", vol])

    for name in os.environ:
        if name.startswith("MQ_"):
            docker_args.extend(["-e", name])

    docker_args.append(image)
    docker_args.extend(["bash", "-c", test_cmd])

    print(f"Language: {lang or '<none>'}")
    print(f"Image:    {image}")
    print(f"Command:  {test_cmd}")
    if network:
        print(f"Network:  {network}")
    print("---")

    return docker_args


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    repo_root = git.repo_root()
    lang = _detect_language(repo_root)

    if not lang and not os.environ.get("DOCKER_DEV_IMAGE"):
        print(
            "ERROR: could not detect project language from repo contents.",
            file=sys.stderr,
        )
        print("Set DOCKER_DEV_IMAGE and DOCKER_TEST_CMD explicitly.", file=sys.stderr)
        return 1

    docker_args = build_docker_args(repo_root, lang)
    os.execvp("docker", docker_args)  # noqa: S606, S607
    return 0  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
