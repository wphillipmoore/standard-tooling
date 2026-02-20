# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Auto-memory policy

**Do NOT use MEMORY.md.** Claude Code's auto-memory feature stores behavioral
rules outside of version control, making them invisible to code review,
inconsistent across repos, and unreliable across sessions. All behavioral rules,
conventions, and workflow instructions belong in managed, version-controlled
documentation (CLAUDE.md, AGENTS.md, skills, or docs/).

If you identify a pattern, convention, or rule worth preserving:

1. **Stop.** Do not write to MEMORY.md.
2. **Discuss with the user** what you want to capture and why.
3. **Together, decide** the correct managed location (CLAUDE.md, a skill file,
   standards docs, or a new issue to track the gap).

This policy exists because MEMORY.md is per-directory and per-machine — it
creates divergent agent behavior across the multi-repo environment this project
operates in. Consistency requires all guidance to live in shared, reviewable
documentation.

## Shell command policy

**Do NOT use heredocs** (`<<EOF` / `<<'EOF'`) for multi-line arguments to CLI
tools such as `gh`, `git commit`, or `curl`. Heredocs routinely fail due to
shell escaping issues with apostrophes, backticks, and special characters.
Always write multi-line content to a temporary file and pass it via `--body-file`
or `--file` instead.

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

### Deployment Before Sync (mandatory)

Consuming repos' CI runs `sync-tooling.sh --check` against the
**latest tagged release** (not `develop`). If you sync consuming
repos before tagging a new release, their CI will fail because the
tag still points to the old managed-files list.

**Required ordering when changing managed scripts:**

1. Merge changes to `standard-tooling` `develop` (feature PR).
2. Create a release PR to `main`, merge it, and **tag the new
   version** (e.g., `v1.0.5`).
3. **Only then** sync consuming repos with
   `sync-tooling.sh --fix`.

Never sync consuming repos from `develop` or an unreleased ref
unless you accept that their CI will fail until the release is
tagged.

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

## Commit and PR Scripts

**NEVER use raw `git commit`** — always use `scripts/dev/commit.sh`.
**NEVER use raw `gh pr create`** — always use `scripts/dev/submit-pr.sh`.

### Committing

```bash
scripts/dev/commit.sh --type feat --scope lint --message "add new check" --agent claude
scripts/dev/commit.sh --type fix --message "correct regex pattern" --agent claude
scripts/dev/commit.sh --type docs --message "update README" --body "Expanded usage section" --agent claude
```

- `--type` (required): `feat|fix|docs|style|refactor|test|chore|ci|build`
- `--message` (required): commit description
- `--agent` (required): `claude` or `codex` — resolves the correct `Co-Authored-By` identity
- `--scope` (optional): conventional commit scope
- `--body` (optional): detailed commit body

### Submitting PRs

```bash
scripts/dev/submit-pr.sh --issue 42 --summary "Add new lint check for X"
scripts/dev/submit-pr.sh --issue 42 --linkage Ref --summary "Update docs" --docs-only
scripts/dev/submit-pr.sh --issue 42 --summary "Fix regex bug" --notes "Tested on macOS and Linux"
```

- `--issue` (required): GitHub issue number (just the number)
- `--summary` (required): one-line PR summary
- `--linkage` (optional, default: `Fixes`): `Fixes|Closes|Resolves|Ref`
- `--title` (optional): PR title (default: most recent commit subject)
- `--notes` (optional): additional notes
- `--docs-only` (optional): applies docs-only testing exception
- `--dry-run` (optional): print generated PR without executing

## Key References

**Canonical Standards**: <https://github.com/wphillipmoore/standards-and-conventions>

- Local path (preferred): `../standards-and-conventions`
- Load all skills from: `<standards-repo-path>/skills/**/SKILL.md`

**User Overrides**: `~/AGENTS.md` (optional, applied if present and readable)
