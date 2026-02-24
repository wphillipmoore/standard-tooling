"""Automate release preparation: branch, changelog, PR, auto-merge.

Shared script for library repositories using the library-release branching
model. Auto-detects the ecosystem to find the version source of truth.

Supported ecosystems:
  - Python: reads version from pyproject.toml
  - Maven:  reads version from pom.xml
  - Go:     reads version from **/version.go
  - Ruby:   reads version from **/version.rb
  - VERSION file: reads version from VERSION (fallback)
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from standard_tooling.lib import git, github

# -- ecosystem detection -----------------------------------------------------


def _detect_python() -> str | None:
    path = Path("pyproject.toml")
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def _detect_maven() -> str | None:
    path = Path("pom.xml")
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<artifactId>[^<]+</artifactId>\s*<version>([^<]+)</version>", text)
    return match.group(1) if match else None


def _detect_go() -> str | None:
    if not Path("go.mod").is_file():
        return None
    for path in Path().rglob("version.go"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r'(?:const\s+)?Version\s*=\s*"([^"]+)"', text)
        if match:
            return match.group(1)
    return None


def _detect_ruby() -> str | None:
    if not Path("Gemfile").is_file():
        return None
    for path in Path().rglob("version.rb"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]", text)
        if match:
            return match.group(1)
    return None


def _detect_version_file() -> str | None:
    path = Path("VERSION")
    if not path.is_file():
        return None
    version = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        msg = (
            f"VERSION file contains '{version}' which is not valid semver.\n"
            f"Expected format: MAJOR.MINOR.PATCH (e.g. 1.2.3)"
        )
        raise SystemExit(msg)
    return version


_Detector = Callable[[], str | None]

_DETECTORS: list[tuple[str, _Detector]] = [
    ("python", _detect_python),
    ("maven", _detect_maven),
    ("go", _detect_go),
    ("ruby", _detect_ruby),
    ("version-file", _detect_version_file),
]


def detect_ecosystem() -> tuple[str, str]:
    """Return (ecosystem_name, version) or fail."""
    for name, detector in _DETECTORS:
        version = detector()
        if version is not None:
            return name, version
    msg = (
        "Could not detect ecosystem. Expected one of:\n"
        "  - pyproject.toml with version (Python)\n"
        "  - pom.xml with version (Maven)\n"
        "  - go.mod + **/version.go (Go)\n"
        "  - Gemfile + **/version.rb (Ruby)\n"
        "  - VERSION file with MAJOR.MINOR.PATCH"
    )
    raise SystemExit(msg)


# -- precondition checks ----------------------------------------------------


def _ensure_on_develop() -> None:
    branch = git.current_branch()
    if branch != "develop":
        raise SystemExit(f"Must be on develop branch (currently on '{branch}').")


def _ensure_clean_tree() -> None:
    status = git.read_output("status", "--porcelain")
    if status:
        raise SystemExit("Working tree is not clean. Commit or stash changes first.")


def _ensure_develop_up_to_date() -> None:
    git.run("fetch", "origin", "develop")
    local_sha = git.read_output("rev-parse", "HEAD")
    remote_sha = git.read_output("rev-parse", "origin/develop")
    if local_sha != remote_sha:
        raise SystemExit(
            f"Local develop ({local_sha[:8]}) does not match "
            f"origin/develop ({remote_sha[:8]}). "
            f"Pull latest changes before preparing a release."
        )


def _ensure_tool(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"Required tool '{name}' not found on PATH.")


# -- release steps -----------------------------------------------------------


def _create_release_branch(branch: str) -> None:
    if git.ref_exists(branch) or git.ref_exists(f"origin/{branch}"):
        raise SystemExit(f"Release branch '{branch}' already exists.")
    print(f"Creating branch: {branch} (from develop)")
    git.run("checkout", "-b", branch)


def _merge_main(version: str) -> None:
    print("Merging main into release branch...")
    git.run("fetch", "origin", "main")
    git.run(
        "merge",
        "origin/main",
        "-X",
        "ours",
        "-m",
        f"chore: merge main into release/{version}",
    )


def _generate_changelog(version: str) -> None:
    for tool in ("git-cliff", "markdownlint"):
        _ensure_tool(tool)
    tag = f"develop-v{version}"
    print(f"Generating changelog with boundary tag: {tag}")
    subprocess.run(("git-cliff", "--tag", tag, "-o", "CHANGELOG.md"), check=True)  # noqa: S603, S607
    changelog = Path("CHANGELOG.md")
    changelog.write_text(changelog.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")
    result = subprocess.run(  # noqa: S603, S607
        ("markdownlint", "CHANGELOG.md"), capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(
            "CHANGELOG.md failed markdownlint validation. "
            "Fix cliff.toml template or CHANGELOG content before releasing."
        )
    git.run("add", "CHANGELOG.md")
    status = git.read_output("status", "--porcelain")
    if not status:
        raise SystemExit(
            f"No publishable changes since the last release.\n"
            f"All commits after develop-v{version} are filtered by git-cliff.\n"
            f"Aborting release preparation."
        )
    git.run("commit", "-m", f"chore: prepare release {version}")


def _create_pr(version: str, issue: int) -> str:
    import tempfile

    print("Creating pull request to main...")
    title = f"release: {version}"
    body = (
        f"## Summary\n\nRelease {version}\n\nRef #{issue}\n\nGenerated with `st-prepare-release`\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(body)
        tmp_path = f.name
    try:
        url = github.create_pr(base="main", title=title, body_file=tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    print(f"PR created: {url}")
    return url


# -- main --------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Prepare a release.")
    parser.add_argument(
        "--issue",
        type=int,
        required=True,
        help="GitHub issue number for release tracking (used for PR linkage).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    _ensure_on_develop()
    _ensure_clean_tree()
    _ensure_develop_up_to_date()
    _ensure_tool("gh")

    ecosystem, version = detect_ecosystem()
    branch = f"release/{version}"

    print(f"Preparing release {version} ({ecosystem})")

    _create_release_branch(branch)
    _merge_main(version)
    _generate_changelog(version)
    print(f"Pushing branch: {branch}")
    git.run("push", "-u", "origin", branch)
    url = _create_pr(version, args.issue)
    github.auto_merge(url, strategy="--merge")

    git.run("checkout", "develop")

    print(f"Release {version} preparation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
