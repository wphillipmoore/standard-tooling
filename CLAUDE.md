# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Documentation Strategy

This repository uses two complementary approaches for AI agent guidance:

- **AGENTS.md**: Generic AI agent instructions using include directives to force documentation indexing. Contains canonical standards references, shared skills loading, and user override support.
- **CLAUDE.md** (this file): Claude Code-specific guidance with prescriptive commands, architecture details, and development workflows optimized for `/init`.

<!-- include: docs/repository-standards.md -->

## Project Overview

This is the canonical source for shared scripts used across all managed repositories: lint scripts, git hooks, and development automation. Changes here propagate to consuming repositories via `sync-tooling.sh`.

**Project name**: standard-tooling

**Status**: Stable (v1.x)

**Canonical Standards**: This repository follows standards at <https://github.com/wphillipmoore/standards-and-conventions> (local path: `../standards-and-conventions` if available)

## Development Commands

### Environment Setup

- **Git hooks**: `git config core.hooksPath scripts/git-hooks` (required before committing)
- **markdownlint**: `npm install --global markdownlint-cli`
- **shellcheck**: `brew install shellcheck`

### Validation

```bash
scripts/lint/markdown-standards.sh   # Canonical validation (markdownlint + structural checks)
shellcheck scripts/lint/*.sh scripts/dev/*.sh scripts/git-hooks/*  # Shell script lint
```

## Architecture

### Script Categories

- **`scripts/git-hooks/`** — Pre-commit (branch naming) and commit-msg (conventional commits, co-author validation) hooks
- **`scripts/lint/`** — Validation scripts for markdown, commit messages, co-author trailers, PR issue linkage, and repository profiles
- **`scripts/dev/`** — Development automation: `sync-tooling.sh` (sync mechanism), `prepare_release.py` (release prep), `finalize_repo.sh` (post-merge cleanup)

### Sync Mechanism

`sync-tooling.sh` keeps consuming repositories synchronized with this canonical source:

- **`--check`** (default): Reports whether local copies are stale
- **`--fix`**: Updates local copies from this repository
- **`--ref TAG`**: Pin to a specific standard-tooling version
- **`--actions-compat`**: Also sync lint scripts to `actions/standards-compliance/scripts/` (for standard-actions)

### Managed Files

All git hooks, all lint scripts, `prepare_release.py`, `finalize_repo.sh`, and `sync-tooling.sh` itself are managed. Consuming repos must not modify these files directly.

### Key Constraints

- **Portability**: Scripts must work on both macOS and Linux
- **shellcheck clean**: All scripts must pass shellcheck
- **No repo-specific logic**: Scripts must work in any consuming repository
- **`skip-sync-check`**: This repo uses `skip-sync-check: "true"` in CI because it IS the canonical tooling source — staleness detection would be circular

## Branching and PR Workflow

- **Protected branches**: `main`, `develop` — no direct commits (enforced by pre-commit hook)
- **Branch naming**: `feature/*`, `bugfix/*`, or `hotfix/*` only
- **Feature/bugfix PRs** target `develop` with squash merge: `gh pr merge --auto --squash --delete-branch`
- **Release PRs** target `main` with regular merge: `gh pr merge --auto --merge --delete-branch`
- **Pre-flight**: Always check branch with `git status -sb` before modifying files. If on `develop`, create a `feature/*` branch first.

## Key References

**Canonical Standards**: <https://github.com/wphillipmoore/standards-and-conventions>

- Local path (preferred): `../standards-and-conventions`
- Load all skills from: `<standards-repo-path>/skills/**/SKILL.md`

**User Overrides**: `~/AGENTS.md` (optional, applied if present and readable)
