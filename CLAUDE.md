# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in
this repository.

<!-- include: docs/repository-standards.md -->

## Auto-memory policy

**Do NOT use MEMORY.md.** Never write to MEMORY.md or any file under the
memory directory. All behavioral rules, conventions, and workflow instructions
belong in managed, version-controlled documentation (CLAUDE.md, AGENTS.md,
skills, or docs/). If you want to persist something, tell the human what you
would save and let them decide where it belongs.

## Project Overview

This is a Python package providing shared development tooling for all managed
repositories: CLI tools for commits, PRs, releases, and validation; bash
validators and git hooks consumed via PATH from a sibling checkout (local) or
CI checkout (GitHub Actions).

**Project name**: standard-tooling

**Status**: Stable (v1.x)

**Canonical Standards**: This repository follows standards at
<https://github.com/wphillipmoore/standards-and-conventions>
(local path: `../standards-and-conventions` if available)

## Development Commands

### Environment Setup

This repository uses a **dual-venv** model:

- **`.venv`** — Created inside dev containers. Shebang paths reference
  `/workspace/.venv/...` and do not work on the host.
- **`.venv-host`** — Created on the host for bootstrap tools like
  `st-docker-run`. Shebang paths reference the real host Python.

```bash
# Host bootstrap (one-time) — provides st-docker-run on the host
UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev

# Enable git hooks
git config core.hooksPath scripts/lib/git-hooks

# Put host tools on PATH
export PATH="$(pwd)/.venv-host/bin:$(pwd)/scripts/bin:$PATH"
```

After the host venv is set up, use `st-docker-run` to run all commands
inside the dev container. See [Validation](#validation) below.

### Validation

```bash
st-docker-run -- uv run st-validate-local              # Runs all checks
```

This is the **only** validation command. Do not run individual linters,
formatters, or other tools outside of `st-validate-local`. If a tool is not
invoked by `st-validate-local`, it is not part of the validation pipeline.

### Three-Tier CI Model

Testing is split across three tiers with increasing scope and cost:

**Tier 1 — Local pre-commit (seconds):** Fast smoke tests in a single
container. Run before every commit. No matrix.

```bash
./scripts/dev/test.sh        # pytest + 100% coverage in dev-python:3.12
./scripts/dev/lint.sh        # ruff check + format in dev-python:3.12
./scripts/dev/audit.sh       # uv lock --check in dev-python:3.12
```

**Tier 2 — Push CI (~1-2 min):** Triggers automatically on push to
`feature/**`, `bugfix/**`, `hotfix/**`, `chore/**`. Single Python version
(3.12), no security scanners or release gates.
Workflow: `.github/workflows/ci-push.yml` (calls `ci.yml`).

**Tier 3 — PR CI (~5-8 min):** Triggers on `pull_request`. Python 3.12,
all quality checks, security scanners (CodeQL, Trivy, Semgrep), standards
compliance, and release gates.
Workflow: `.github/workflows/ci.yml`.

### Docker-First Testing

All tests can run inside containers — Docker is the only host prerequisite.
Dev container images are maintained in
[standard-tooling-docker](https://github.com/wphillipmoore/standard-tooling-docker).

```bash
# Build the dev image (one-time)
cd ../standard-tooling-docker && docker/build.sh

# Run unit tests in container
./scripts/dev/test.sh

# Run linter in container
./scripts/dev/lint.sh

# Run dependency audit in container
./scripts/dev/audit.sh
```

Environment overrides:

- `DOCKER_DEV_IMAGE` — override the container image
  (default: `ghcr.io/wphillipmoore/dev-python:3.12`)
- `DOCKER_TEST_CMD` — override the test command

## Architecture

### Python Package (`src/standard_tooling/`)

CLI tools installed as `st-*` console scripts:

- **`st-commit`** — Construct standards-compliant conventional
  commits with co-author resolution
- **`st-submit-pr`** — Create standards-compliant PRs with auto-merge
- **`st-prepare-release`** — Automate release preparation (branch, changelog, PR)
- **`st-finalize-repo`** — Post-merge cleanup (branch deletion, remote pruning)
- **`st-validate-local`** — Driver for pre-PR local validation
- **`st-ensure-label`** — Idempotent GitHub label creation
- **`st-list-project-repos`** — List repos linked to a GitHub Project
- **`st-set-project-field`** — Set single-select field on GitHub Project item
- **`st-docker-run`** — Run arbitrary commands inside a dev container
- **`st-docker-test`** — Run repo test suite inside a dev container

Shared libraries under `src/standard_tooling/lib/`:

- **`git.py`** — Git subprocess wrappers
- **`github.py`** — gh CLI subprocess wrappers
- **`repo_profile.py`** — Parse `docs/repository-standards.md`

### Bash Scripts (`scripts/bin/`)

Grandfathered validators consumed via PATH (no `.sh` extensions):

- `markdown-standards` — markdownlint + structural checks
- `repo-profile` — repository profile validation
- `pr-issue-linkage` — PR body issue linkage validation
- `validate-local-common` — shared validation checks
  (shellcheck, markdownlint, repo-profile)
- `validate-local-python` — Python-specific validation
- `validate-local-go` — Go-specific validation
- `validate-local-java` — Java-specific validation

### Docker Dev Images

Dev container images (Dockerfiles, build script, publish workflow) are
maintained in [standard-tooling-docker](https://github.com/wphillipmoore/standard-tooling-docker).

The `st-docker-test` entry point auto-detects the project
language (Gemfile, pyproject.toml, go.mod, pom.xml/mvnw) and runs the test
suite inside the appropriate container. Consuming repos call it directly or wrap
it in a thin `scripts/dev/test.sh`. Environment overrides:

- `DOCKER_DEV_IMAGE` — override the container image
- `DOCKER_TEST_CMD` — override the test command
- `DOCKER_NETWORK` — join a Docker network (e.g., for MQ integration tests)
- `MQ_*` env vars are automatically passed through to the container

### Git Hooks (`scripts/lib/git-hooks/`)

Consumed via `git config core.hooksPath scripts/lib/git-hooks`:

- `pre-commit` — Branch naming enforcement

### Consumption Model

**Dev containers** (primary): All `st-*` entry points are pre-installed in
the dev container images (`dev-python`, `dev-java`, `dev-go`, `dev-rust`,
`dev-ruby`, `dev-base`). No local setup required.

**Host bootstrap** (for `st-docker-run`): The host needs `st-docker-run`
to bridge into containers. Consuming repos locate it by searching:

1. `../standard-tooling/.venv-host/bin/st-docker-run` (sibling checkout)
2. `st-docker-run` on PATH (installed globally)

One-time setup in the `standard-tooling` checkout:

```bash
UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev
```

**Git hooks** (any consuming repo):

```bash
git config core.hooksPath ../standard-tooling/scripts/lib/git-hooks
```

**CI (GitHub Actions)**: The `standards-compliance` action clones
standard-tooling and puts `scripts/bin/` on PATH. The bash wrappers
include a PYTHONPATH fallback for non-installed environments.

### Key Constraints

- **Portability**: Scripts must work on both macOS and Linux
- **shellcheck clean**: All bash scripts must pass shellcheck
- **No repo-specific logic**: Scripts must work in any consuming repository
