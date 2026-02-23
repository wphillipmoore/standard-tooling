# Standard Tooling

## Table of Contents

- [Purpose](#purpose)
- [Installation](#installation)
- [CLI tools](#cli-tools)
- [Bash validators](#bash-validators)
- [Git hooks](#git-hooks)
- [Releasing](#releasing)

## Purpose

Shared development tooling for all managed repositories. Structured as a
Python package with CLI entry points (`st-*`) and grandfathered bash
validators, consumed via PATH from a sibling checkout (local) or CI checkout
(GitHub Actions).

## Installation

### Local development

```bash
cd standard-tooling
uv sync --group dev
export PATH="$(pwd)/.venv/bin:$(pwd)/scripts/bin:$PATH"
git config core.hooksPath scripts/lib/git-hooks
```

### CI (GitHub Actions)

```yaml
- uses: actions/checkout@v4
  with:
    repository: wphillipmoore/standard-tooling
    ref: v1.2
    path: .standard-tooling

- name: Set up standard-tooling
  run: |
    cd .standard-tooling && uv sync --frozen
    echo "$GITHUB_WORKSPACE/.standard-tooling/.venv/bin" >> "$GITHUB_PATH"
    echo "$GITHUB_WORKSPACE/.standard-tooling/scripts/bin" >> "$GITHUB_PATH"
```

## CLI tools

- `st-commit` — Standards-compliant conventional commits
- `st-submit-pr` — Standards-compliant PR creation with auto-merge
- `st-prepare-release` — Automated release preparation
- `st-finalize-repo` — Post-merge cleanup
- `st-validate-local` — Pre-PR local validation driver
- `st-ensure-label` — Idempotent GitHub label creation
- `st-list-project-repos` — List repos linked to a GitHub Project
- `st-set-project-field` — Set field on a GitHub Project item

## Bash validators

Grandfathered bash scripts in `scripts/bin/` consumed via PATH:

- `markdown-standards` — markdownlint + structural checks
- `repo-profile` — repository profile validation
- `pr-issue-linkage` — PR body issue linkage validation
- `commit-message` — single commit message validation
- `validate-local-common` — shared checks for all repos
- `validate-local-python` — Python-specific validation
- `validate-local-go` — Go-specific validation
- `validate-local-java` — Java-specific validation

## Git hooks

Consumed via `git config core.hooksPath scripts/lib/git-hooks`:

- `pre-commit` — branch naming enforcement
- `commit-msg` — Conventional Commits validation

## Releasing

Tag releases on `main` using semantic versioning. The release process
publishes both a full tag (`v1.2.0`) and a rolling `v{major}.{minor}` tag
(`v1.2`) that always points to the latest patch. Consuming repos pin to the
`v{major}.{minor}` tag in CI.
