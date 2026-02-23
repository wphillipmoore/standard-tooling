# Standard Tooling

Standard-tooling is a Python package and script collection providing shared
development tooling for all managed repositories. It delivers CLI tools for
commits, PRs, releases, and validation alongside bash validators and git hooks
-- all consumed via PATH.

## Components

**Python CLI tools** (`src/standard_tooling/`):
`st-commit`, `st-submit-pr`, `st-prepare-release`,
`st-finalize-repo`, `st-validate-local`

**Bash validators** (`scripts/bin/`):
`commit-message`, `repo-profile`, `markdown-standards`,
`pr-issue-linkage`, validation drivers

**Git hooks** (`scripts/lib/git-hooks/`):
Branch naming enforcement, commit message validation

## Design Principles

- **Portability** -- scripts run on both macOS and Linux
- **shellcheck clean** -- all shell scripts pass shellcheck
- **No repo-specific logic** -- every script works in any consuming
  repository
- **PATH-based consumption** -- consuming repos add standard-tooling to
  PATH rather than copying files

## How It Works

1. Standard-tooling is cloned as a sibling directory (local development)
   or checked out in CI (GitHub Actions).
2. The Python package is installed via `uv sync`, making `st-*` CLI
   tools available in `.venv/bin/`.
3. Both `.venv/bin/` and `scripts/bin/` are added to PATH.
4. Git hooks are configured to point at `scripts/lib/git-hooks/`.
5. Consuming repos call tools by bare name -- no file copying or syncing.

## Quick Links

- [Getting Started](getting-started.md) -- set up a consuming repository
- [Script Reference](reference/index.md) -- documentation for each tool
- [Validation Matrix](guides/validation-matrix.md) -- which checks run where
