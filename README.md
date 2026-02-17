# Standard Tooling

## Table of Contents

- [Purpose](#purpose)
- [Shared scripts](#shared-scripts)
- [Sync mechanism](#sync-mechanism)
- [Releasing](#releasing)

## Purpose

Canonical source for shared scripts used across all repositories. Consuming
repos copy these scripts and use `sync-tooling.sh` to keep them up to date.

## Shared scripts

### Git hooks (local-only)

- `scripts/git-hooks/commit-msg` — Conventional Commits + co-author validation
- `scripts/git-hooks/pre-commit` — branch naming enforcement

### Lint scripts (hooks + CI)

- `scripts/lint/co-author.sh` — co-author trailer validation
- `scripts/lint/commit-message.sh` — single commit message validation
- `scripts/lint/commit-messages.sh` — commit range validation (CI)
- `scripts/lint/markdown-standards.sh` — markdownlint + structural checks
- `scripts/lint/pr-issue-linkage.sh` — PR body issue linkage validation
- `scripts/lint/repo-profile.sh` — repository profile validation

### Dev scripts

- `scripts/dev/sync-tooling.sh` — sync mechanism (see below)
- `scripts/dev/prepare_release.py` — automated release preparation
- `scripts/dev/finalize_repo.sh` — post-merge cleanup

## Sync mechanism

Each consuming repo copies `scripts/dev/sync-tooling.sh` from this
repository. The script compares local copies against the canonical versions
here and can auto-fix drift.

```bash
# Check for staleness (CI gate)
scripts/dev/sync-tooling.sh --check

# Auto-fix stale copies
scripts/dev/sync-tooling.sh --fix

# Sync to a specific tag
scripts/dev/sync-tooling.sh --fix --ref v1.0.0
```

The `--actions-compat` flag additionally syncs lint scripts to
`actions/standards-compliance/scripts/` for standard-actions.

## Releasing

Tag releases on `main` using semantic versioning. Consuming repos pin to
tags via `--ref`. The CI staleness gate compares against the latest tag
by default.

