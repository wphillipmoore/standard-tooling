# Standard Tooling

Standard-tooling is the canonical source for shared scripts used across all
managed repositories. It provides git hooks, lint scripts, and development
automation that enforce consistent standards.

## Script Categories

| Category | Path | Purpose |
| -------- | ---- | ------- |
| **Git Hooks** | `scripts/git-hooks/` | Branch naming, commit-msg checks |
| **Lint Scripts** | `scripts/lint/` | Markdown, commit, co-author, PR |
| **Dev Scripts** | `scripts/dev/` | Commit, PR, sync, release, finalization |

## Design Principles

- **Portability** -- scripts run on both macOS and Linux
- **shellcheck clean** -- all shell scripts pass shellcheck
- **No repo-specific logic** -- every script works in any consuming
  repository
- **Single source of truth** -- consuming repos sync from this
  repository via `sync-tooling.sh` and must not modify managed files
  directly

## How It Works

1. This repository defines the canonical version of each managed
   script.
2. Consuming repos run `sync-tooling.sh --check` in CI to detect
   drift.
3. When scripts change, a new version is tagged and consumers run
   `sync-tooling.sh --fix` to update.

## Managed Files

Standard-tooling currently manages 18 files:

- 2 git hooks (`pre-commit`, `commit-msg`)
- 6 lint scripts
- 10 dev scripts (including language-specific validation variants)

See the [Script Reference](reference/index.md) for the full list.
