# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

<!-- include: docs/repository-standards.md -->

## Project Overview

This is a Python package providing shared development tooling for all managed
repositories: CLI tools for commits, PRs, releases, and validation; bash
validators and git hooks consumed via PATH from a sibling checkout (local) or
CI checkout (GitHub Actions).

**Project name**: standard-tooling

**Status**: Stable (v1.x)

**Canonical Standards**: This repository follows standards at <https://github.com/wphillipmoore/standards-and-conventions> (local path: `../standards-and-conventions` if available)

## Development Commands

### Environment Setup

```bash
uv sync --group dev                                    # Install package + dev deps
git config core.hooksPath scripts/lib/git-hooks        # Enable git hooks
export PATH="$(pwd)/.venv/bin:$(pwd)/scripts/bin:$PATH" # Put tools on PATH
```

### Validation

```bash
uv run ruff check src/ tests/                          # Lint Python
uv run ruff format --check .                           # Check formatting
uv run mypy src/                                       # Type check
uv run pytest tests/ -v                                # Run tests
shellcheck scripts/bin/* scripts/lib/git-hooks/*       # Shell script lint
```

### Quick full validation

```bash
uv run st-validate-local                               # Runs all checks
```

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

- `DOCKER_DEV_IMAGE` — override the container image (default: `dev-python:3.12`)
- `DOCKER_TEST_CMD` — override the test command

## Architecture

### Python Package (`src/standard_tooling/`)

CLI tools installed as `st-*` console scripts:

- **`st-commit`** — Construct standards-compliant conventional commits with co-author resolution
- **`st-submit-pr`** — Create standards-compliant PRs with auto-merge
- **`st-prepare-release`** — Automate release preparation (branch, changelog, PR)
- **`st-finalize-repo`** — Post-merge cleanup (branch deletion, remote pruning)
- **`st-validate-local`** — Driver for pre-PR local validation
- **`st-ensure-label`** — Idempotent GitHub label creation
- **`st-list-project-repos`** — List repos linked to a GitHub Project
- **`st-set-project-field`** — Set single-select field on GitHub Project item

Shared libraries under `src/standard_tooling/lib/`:

- **`git.py`** — Git subprocess wrappers
- **`github.py`** — gh CLI subprocess wrappers
- **`repo_profile.py`** — Parse `docs/repository-standards.md`

### Bash Scripts (`scripts/bin/`)

Grandfathered validators consumed via PATH (no `.sh` extensions):

- `markdown-standards` — markdownlint + structural checks
- `repo-profile` — repository profile validation
- `pr-issue-linkage` — PR body issue linkage validation
- `commit-message` — single commit message validation
- `validate-local-common` — shared validation checks (shellcheck, markdownlint, repo-profile)
- `validate-local-python` — Python-specific validation
- `validate-local-go` — Go-specific validation
- `validate-local-java` — Java-specific validation
- `docker-test` — run repo test suite inside a dev container

### Docker Dev Images

Dev container images (Dockerfiles, build script, publish workflow) are
maintained in [standard-tooling-docker](https://github.com/wphillipmoore/standard-tooling-docker).

The `docker-test` script (`scripts/bin/docker-test`) auto-detects the project
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
- `commit-msg` — Conventional Commits validation

### Consumption Model

**Local development** (any consuming repo):

```bash
cd ../standard-tooling && uv sync
export PATH="../standard-tooling/.venv/bin:../standard-tooling/scripts/bin:$PATH"
git config core.hooksPath ../standard-tooling/scripts/lib/git-hooks
```

**CI (GitHub Actions)**:

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

### Key Constraints

- **Portability**: Scripts must work on both macOS and Linux
- **shellcheck clean**: All bash scripts must pass shellcheck
- **No repo-specific logic**: Scripts must work in any consuming repository
