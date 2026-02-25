# Three-Tier CI Architecture

This guide explains the three-tier continuous integration model used
across all `mq-rest-admin-*` repositories, and how to implement it in
new projects.

## Table of Contents

- [Overview](#overview)
- [Tier 1: Local pre-commit](#tier-1-local-pre-commit)
- [Tier 2: Push CI](#tier-2-push-ci)
- [Tier 3: PR CI](#tier-3-pr-ci)
- [Architecture](#architecture)
- [Implementation guide](#implementation-guide)
- [CI gates](#ci-gates)
- [Dev container images](#dev-container-images)

## Overview

Testing is split into three tiers with increasing scope, cost, and
feedback latency:

| Tier | Trigger | Time | Security |
| ---- | ------- | ---- | -------- |
| 1 | Manual (before commit) | Seconds | No |
| 2 | Push to feature branch | ~3-5 min | No |
| 3 | Pull request | ~8-10 min | Yes |

- **Tier 1**: Single version, unit tests only
- **Tier 2**: Single version, unit + integration tests
- **Tier 3**: Full version matrix, all checks

The goal is fast local feedback for the developer, rapid push-to-CI
validation before PR submission, and comprehensive gated checks on the
PR itself.

## Tier 1: Local pre-commit

Run in a dev container on the developer's machine. Docker is the only
host prerequisite.

```bash
./scripts/dev/test.sh        # Unit tests + linting
./scripts/dev/lint.sh        # Lint and formatting checks
./scripts/dev/audit.sh       # Dependency and license audit
```

Each script follows the same pattern:

1. Set `DOCKER_DEV_IMAGE` (default: `dev-<language>:<latest-version>`)
2. Set `DOCKER_TEST_CMD` (language-specific command)
3. Delegate to `docker-test` if available, otherwise run `docker run`
   directly

Environment overrides:

- `DOCKER_DEV_IMAGE` — use a different container image
- `DOCKER_TEST_CMD` — override the test command

!!! tip
    Build the dev images locally before first use:
    `cd ../standard-tooling && docker/build.sh`

## Tier 2: Push CI

Triggers automatically on push to `feature/**`, `bugfix/**`,
`hotfix/**`, or `chore/**` branches.

**What runs:**

- Unit tests (single latest version)
- Integration tests (single latest version)
- Dependency audit

**What is skipped:**

- Security scanners (CodeQL, Trivy, Semgrep)
- Standards compliance
- Release gates
- Full version matrix

The workflow file is `.github/workflows/ci-push.yml`, a thin wrapper
that calls `ci.yml` with restricted inputs:

```yaml
name: CI (push)

on:
  push:
    branches:
      - "feature/**"
      - "bugfix/**"
      - "hotfix/**"
      - "chore/**"

permissions:
  contents: read
  security-events: write

jobs:
  ci:
    uses: ./.github/workflows/ci.yml
    permissions:
      contents: read
      security-events: write
    with:
      versions: '["<latest>"]'
      integration-matrix: '[{...single entry...}]'
      run-security: "false"
      run-release-gates: "false"
```

## Tier 3: PR CI

Triggers on `pull_request` events. Runs the full validation suite.

**What runs:**

- Unit tests across the full version matrix
- Integration tests across the full version matrix
- Security scanners (CodeQL, Trivy, Semgrep) via shared reusable workflow
- Standards compliance
- Dependency audit
- Release gates (version divergence, format validation)

The workflow file is `.github/workflows/ci.yml`, which doubles as both
the direct PR trigger and a reusable workflow via `workflow_call`.

## Architecture

### Reusable workflow pattern

`ci.yml` accepts `workflow_call` with inputs that control scope:

| Input | Type | Default |
| ----- | ---- | ------- |
| `versions` | string (JSON) | Full matrix |
| `integration-matrix` | string (JSON) | Full matrix |
| `run-security` | string | `"true"` |
| `run-release-gates` | string | `"true"` |

- `versions` — language versions to test
- `integration-matrix` — test entries with ports
- `run-security` — enable security scanners
- `run-release-gates` — enable release gate checks

When triggered directly by `pull_request`, all inputs are empty and
defaults produce the full Tier 3 behavior. When called from
`ci-push.yml`, inputs restrict scope to Tier 2.

!!! warning "String inputs, not booleans"
    Use `type: string` for gate inputs, not `type: boolean`. Boolean
    inputs are unreliable for job-level `if` conditions when the
    workflow is triggered directly (inputs are empty, not `false`).
    Use `!= 'false'` comparisons instead.

### Shared security workflow

Security scanners and standards compliance are factored into a shared
reusable workflow at
`wphillipmoore/standard-actions/.github/workflows/ci-security.yml`.

This provides four jobs:

- `ci: standards-compliance`
- `security: codeql`
- `security: trivy`
- `security: semgrep`

Call it from `ci.yml`:

```yaml
security-and-standards:
  if: ${{ inputs.run-security != 'false' }}
  uses: wphillipmoore/standard-actions/.github/workflows/ci-security.yml@develop
  with:
    language: ruby
    # For Go, also set: semgrep-language: golang
  permissions:
    contents: read
    security-events: write
```

!!! tip "Semgrep language names"
    Semgrep uses `p/<language>` rulesets. Most languages match their
    common name (`ruby`, `python`, `java`) but Go requires `golang`.
    Use the `semgrep-language` input to override when needed.

### Default matrix pattern

Use `fromJSON()` with a fallback to embed the full default matrix
directly in the workflow:

```yaml
strategy:
  fail-fast: false
  matrix:
    version: ${{ fromJSON(inputs.versions || '["3.2", "3.3", "3.4"]') }}
```

This avoids needing a separate job to compute the matrix.

## Implementation guide

### Step 1: Convert ci.yml to reusable workflow

Add `workflow_call` alongside `pull_request` in the `on:` block. Define
inputs with string types and sensible defaults.

### Step 2: Create ci-push.yml

Create a thin wrapper that calls `ci.yml` with single-version inputs
and security/release gates disabled.

### Step 3: Factor security into shared workflow

Replace inline CodeQL, Trivy, Semgrep, and standards-compliance jobs
with a single call to `ci-security.yml`.

### Step 4: Add dev scripts

Create `scripts/dev/test.sh`, `scripts/dev/lint.sh`, and
`scripts/dev/audit.sh` following the Docker-first pattern. See
[Dev container images](#dev-container-images) for image details.

### Step 5: Update CI gates

Update the repository ruleset to match new check names. Key changes:

- Remove `ci: docs-only` (no longer exists)
- Replace `ci: standards-compliance` with
  `security-and-standards / ci: standards-compliance`
- Replace `security: *` with `security-and-standards / security: *`

Use the GitHub API to update rulesets:

```bash
gh api repos/OWNER/REPO/rulesets/RULESET_ID -X PUT --input gates.json
```

### Step 6: Update CLAUDE.md

Add three-tier CI model and Docker-first testing sections to the
repository's `CLAUDE.md`.

## CI gates

When security and standards jobs move into the shared reusable workflow,
their check names gain a `security-and-standards /` prefix:

Old names and their replacements:

- `ci: standards-compliance` →
  `security-and-standards / ci: standards-compliance`
- `security: codeql` →
  `security-and-standards / security: codeql`
- `security: trivy` →
  `security-and-standards / security: trivy`
- `security: semgrep` →
  `security-and-standards / security: semgrep`

Jobs that remain inline keep their names unchanged:

- `ci: dependency-audit`
- `release: gates`
- `test: unit (<version>)`
- `test: integration (<version>)`

## Dev container images

Published to `ghcr.io/wphillipmoore/dev-<language>:<version>` from the
`docker/` directory in this repository.

### Available images

**`dev-ruby`** (3.2, 3.3, 3.4)
:   Base: `ruby:<v>-slim`. Includes build-essential,
    git, curl, bundler.

**`dev-python`** (3.12, 3.13, 3.14)
:   Base: `python:<v>-slim`. Includes git, curl, uv.

**`dev-java`** (17, 21)
:   Base: `eclipse-temurin:<v>-jdk`. Includes git, curl.

**`dev-go`** (1.25, 1.26)
:   Base: `golang:<v>`. Includes golangci-lint,
    govulncheck, go-licenses, gocyclo.

### Building locally

```bash
cd ../standard-tooling
docker/build.sh
```

This builds all images. Individual images can be built with:

```bash
docker build --build-arg RUBY_VERSION=3.4 -t dev-ruby:3.4 docker/ruby/
```

### Publishing

Images are published automatically when files under `docker/` change
on the `develop` or `main` branches via
`.github/workflows/docker-publish.yml`.

### Design principles

- **Thin images** — language runtime + package manager + git/curl
- **Project-managed dependencies** — tools come from lockfiles at
  container startup (e.g., `bundle install`, `uv sync`, `go install`)
- **No host requirements** — Docker is the only prerequisite for
  local development
