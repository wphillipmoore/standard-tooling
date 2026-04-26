"""Finalize a repository after a PR merge.

Switches to the target branch, fast-forward pulls, deletes merged local
branches, and prunes stale remote-tracking references.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from standard_tooling.lib import git, repo_profile

_ETERNAL_BY_MODEL: dict[str, list[str]] = {
    "docs-single-branch": ["develop"],
    "library-release": ["develop", "main"],
    "application-promotion": ["develop", "release", "main"],
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Finalize a repository after a PR merge.")
    parser.add_argument("--target-branch", default="develop", help="Target branch to switch to")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    return parser.parse_args(argv)


def _run(args: list[str], *, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] git {' '.join(args)}")
    else:
        git.run(*args)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not git.is_main_worktree():
        print(
            "ERROR: st-finalize-repo must be run from the main worktree, not a secondary one.",
            file=sys.stderr,
        )
        print(
            "  The target branch is already checked out in the main "
            "worktree; git will refuse to check it out a second time.",
            file=sys.stderr,
        )
        print("  Run:  cd <repo-root> && st-finalize-repo", file=sys.stderr)
        return 1

    root = git.repo_root()

    try:
        profile = repo_profile.read_profile(root)
        model = profile.branching_model
    except FileNotFoundError:
        model = ""

    eternal = {"gh-pages"}
    if model in _ETERNAL_BY_MODEL:
        eternal.update(_ETERNAL_BY_MODEL[model])
    elif model == "":
        print("WARNING: branching_model not found; protecting develop and main.", file=sys.stderr)
        eternal.update(("develop", "main"))
    else:
        print(f"ERROR: unrecognized branching_model '{model}'.", file=sys.stderr)
        return 1

    current = git.current_branch()
    if current != args.target_branch:
        print(f"Switching to {args.target_branch}...")
        _run(["checkout", args.target_branch], dry_run=args.dry_run)
    else:
        print(f"Already on {args.target_branch}.")

    print(f"Pulling latest from origin/{args.target_branch}...")
    _run(["fetch", "origin", args.target_branch], dry_run=args.dry_run)
    _run(["pull", "--ff-only", "origin", args.target_branch], dry_run=args.dry_run)

    print("Checking for merged local branches...")
    deleted: list[str] = []
    for branch in git.merged_branches(args.target_branch):
        if branch in eternal:
            continue
        print(f"  Deleting merged branch: {branch}")
        _run(["branch", "-d", branch], dry_run=args.dry_run)
        deleted.append(branch)

    print("Pruning stale remote-tracking references...")
    if args.dry_run:
        print("  [dry-run] git remote prune origin")
    else:
        git.run("remote", "prune", "origin")

    # -- post-finalization validation ------------------------------------------
    # Run canonical validation to catch problems on the target branch before
    # the next PR is created.  Failures are reported as warnings — the
    # finalization itself already succeeded.

    validation_failed = False
    if not args.dry_run:
        docker_run = shutil.which("st-docker-run")
        validator = shutil.which("st-validate-local")

        if docker_run is not None:
            print()
            print("Running post-finalization validation via st-docker-run...")
            cmd: tuple[str, ...] = (docker_run, "--", "st-validate-local")
        elif validator is not None:
            print()
            print("Running post-finalization validation...")
            cmd = (validator,)
        else:
            print()
            print(
                "ERROR: neither st-docker-run nor st-validate-local found on PATH.",
                file=sys.stderr,
            )
            print("  Ensure standard-tooling is installed and on PATH.", file=sys.stderr)
            return 1

        result = subprocess.run(cmd, check=False)  # noqa: S603
        if result.returncode != 0:
            validation_failed = True
    else:
        print("  [dry-run] st-docker-run -- st-validate-local")

    print()
    print("Finalization complete.")
    print(f"  Branch: {args.target_branch}")
    print(f"  Deleted: {' '.join(deleted) if deleted else '(none)'}")
    print("  Remotes: pruned")

    if validation_failed:
        print()
        print("WARNING: post-finalization validation failed.", file=sys.stderr)
        print(f"  The {args.target_branch} branch has issues that should be", file=sys.stderr)
        print("  fixed before creating the next PR.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
