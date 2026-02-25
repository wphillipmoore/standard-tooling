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

### Docker Dev Images (`docker/`)

Language-specific dev containers for Docker-first testing:

- **`docker/ruby/Dockerfile`** — Ruby dev image (`dev-ruby:3.4`)
- **`docker/python/Dockerfile`** — Python dev image with uv (`dev-python:3.14`)
- **`docker/java/Dockerfile`** — Java dev image, Eclipse Temurin (`dev-java:21`)
- **`docker/go/Dockerfile`** — Go dev image with linters (`dev-go:1.23`)
- **`docker/build.sh`** — Builds all images locally for every version in the matrix

#### GHCR Publishing

Images are published to GitHub Container Registry by the `docker-publish.yml`
workflow on push to `develop` or `main` when `docker/**` files change, or via
manual `workflow_dispatch`.

Image naming: `ghcr.io/wphillipmoore/dev-{language}:{version}`

Version matrix:

| Language | Versions |
|----------|----------|
| Ruby     | 3.2, 3.3, 3.4 |
| Python   | 3.13, 3.14 |
| Java     | 21 |
| Go       | 1.23 |

To trigger a rebuild manually: Actions → "Publish dev container images" →
Run workflow.

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

## Branching and PR Workflow

- **Protected branches**: `main`, `develop` — no direct commits (enforced by pre-commit hook)
- **Branch naming**: `feature/*`, `bugfix/*`, `hotfix/*`, `chore/*`, or `release/*` only
- **Feature/bugfix PRs** target `develop` with squash merge
- **Release PRs** target `main` with regular merge
- **Pre-flight**: Always check branch with `git status -sb` before modifying files. If on `develop`, create a `feature/*` branch first.

## Commit and PR Scripts

**NEVER use raw `git commit`** — always use `st-commit`.
**NEVER use raw `gh pr create`** — always use `st-submit-pr`.

### Committing

```bash
st-commit --type feat --scope lint --message "add new check" --agent claude
st-commit --type fix --message "correct regex pattern" --agent claude
st-commit --type docs --message "update README" --body "Expanded usage section" --agent claude
```

- `--type` (required): `feat|fix|docs|style|refactor|test|chore|ci|build`
- `--message` (required): commit description
- `--agent` (required): `claude` or `codex` — resolves the correct `Co-Authored-By` identity
- `--scope` (optional): conventional commit scope
- `--body` (optional): detailed commit body

### Submitting PRs

```bash
st-submit-pr --issue 42 --summary "Add new lint check for X"
st-submit-pr --issue 42 --linkage Ref --summary "Update docs" --docs-only
st-submit-pr --issue 42 --summary "Fix regex bug" --notes "Tested on macOS and Linux"
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
