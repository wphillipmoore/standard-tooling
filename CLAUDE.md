# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in
this repository.

<!-- include: docs/repository-standards.md -->

## Parallel AI agent development

This repository supports running multiple Claude Code agents in parallel via
git worktrees. The convention keeps parallel agents' working trees isolated
while preserving shared project memory (which Claude Code derives from the
session's starting CWD).

**Canonical spec:**
[`docs/specs/worktree-convention.md`](docs/specs/worktree-convention.md) —
full rationale, trust model, failure modes, and memory-path implications.

### Structure

```text
~/dev/github/standard-tooling/           ← sessions ALWAYS start here
  .git/
  CLAUDE.md, src/, docs/, …              ← main worktree (usually `develop`)
  .worktrees/                            ← container for parallel worktrees
    issue-258-worktree-convention/       ← worktree on feature/258-worktree-convention
    …
```

### Rules

1. **Sessions always start at the project root.**
   `cd ~/dev/github/standard-tooling && claude` — never from inside
   `.worktrees/<name>/`. This keeps the memory-path slug stable and shared.
2. **Each parallel agent is assigned exactly one worktree.** The session
   prompt names the worktree (see Agent prompt contract below).
   - For Read / Edit / Write tools: use the worktree's absolute path.
   - For Bash commands that touch files: `cd` into the worktree first,
     or use absolute paths.
3. **The main worktree is read-only.** All edits flow through a worktree
   on a feature branch — the logical endpoint of the standing
   "no direct commits to develop" policy. `st-commit` itself enforces
   this: when a `.worktrees/` directory is present, it refuses commits
   on `feature/**`, `bugfix/**`, `hotfix/**`, or `chore/**` branches
   that originate from the main worktree. The `.githooks/pre-commit`
   gate then refuses any raw `git commit` that bypasses `st-commit`.
4. **One worktree per issue.** Don't stack in-flight issues. When a
   branch lands, remove the worktree before starting the next.
5. **Naming: `issue-<N>-<short-slug>`.** `<N>` is the GitHub issue
   number; `<short-slug>` is 2–4 kebab-case tokens.

### Agent prompt contract

When launching a parallel-agent session, use this template (fill in the
placeholders):

```text
You are working on issue #<N>: <issue title>.

Your worktree is: /Users/pmoore/dev/github/standard-tooling/.worktrees/issue-<N>-<slug>/
Your branch is:   feature/<N>-<slug>

Rules for this session:
- Do all git operations from inside your worktree:
    cd <absolute-worktree-path> && git <command>
- For Read / Edit / Write tools, use the absolute worktree path.
- For Bash commands that touch files, cd into the worktree first
  or use absolute paths.
- Do not edit files at the project root. The main worktree is
  read-only — all changes flow through your worktree on your
  feature branch.
- When you need to run validation, run it from inside your worktree
  (st-docker-run mounts the current directory).
```

All fields are required.

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

# Enable the pre-commit gate (refuses raw `git commit`; admits st-commit)
git config core.hooksPath .githooks

# Put host tools on PATH
export PATH="$(pwd)/.venv-host/bin:$PATH"
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

**Tier 1 — Local pre-commit (seconds):** The single entry point
`st-docker-run -- uv run st-validate-local` runs everything
(lint, typecheck, tests, audit, common checks) inside one dev
container. Run before every commit.

**Tier 2 — Push CI (~1-2 min):** Triggers automatically on push to
`feature/**`, `bugfix/**`, `hotfix/**`, `chore/**`. Single Python version
(3.12), no security scanners or release gates.
Workflow: `.github/workflows/ci-push.yml` (calls `ci.yml`).

**Tier 3 — PR CI (~5-8 min):** Triggers on `pull_request`. Python 3.12,
all quality checks, security scanners (CodeQL, Trivy, Semgrep), standards
compliance, and release gates.
Workflow: `.github/workflows/ci.yml`.

### Docker-First Testing

Docker is the only host prerequisite. The validation stack uses
exactly one container per run:

- **Outer layer**: `st-docker-run` launches the dev container once
  and runs the validation driver inside.
- **Inner layer**: `scripts/dev/{lint,test,typecheck,audit}.sh`
  are tiny, container-local scripts. They assume they are already
  running inside the dev container and invoke tooling directly
  (`uv run ruff check`, `uv run pytest`, etc.). They do **not**
  re-containerize.

Dev container images are maintained in
[standard-tooling-docker](https://github.com/wphillipmoore/standard-tooling-docker).

```bash
# Build the dev image (one-time)
cd ../standard-tooling-docker && docker/build.sh

# Run the full validation pipeline in one container
st-docker-run -- uv run st-validate-local
```

If you need to tweak what validation runs for this repo, edit
`scripts/dev/*.sh` — those scripts are the per-repo customization
point. Keep them container-local (no `st-docker-run`, no
`st-docker-test`, no `DOCKER_*` env vars).

## Architecture

### Python Package (`src/standard_tooling/`)

CLI tools installed as `st-*` console scripts:

- **`st-commit`** — Construct standards-compliant conventional
  commits with co-author resolution
- **`st-submit-pr`** — Create standards-compliant PRs (manual merge)
- **`st-merge-when-green`** — Wait for a PR's checks, then merge it
  (release-workflow use only; normal PRs stay on the honor-system
  manual-merge policy)
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

### Git Hooks (`.githooks/`)

Consumed via `git config core.hooksPath .githooks`:

- `pre-commit` — Env-var-plus-`GIT_REFLOG_ACTION` gate. Admits commits
  with `ST_COMMIT_CONTEXT=1` (set by `st-commit`) and admits derived
  workflows (`amend`, `cherry-pick`, `revert`, `rebase*`, `merge*`).
  Rejects raw `git commit -m "..."`. The five branch / context checks
  (detached HEAD, protected branches, branch prefix, issue number,
  worktree convention) live in `st-commit` itself, not the hook.

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

**Git hooks** (any consuming repo): each repo vendors its own
`.githooks/pre-commit` (the env-var gate from this repo's spec) and
points its `core.hooksPath` at it:

```bash
git config core.hooksPath .githooks
```

**CI (GitHub Actions)**: under the host-level-tool spec, CI uses
the same two paths as developers — Python repos via `uv sync --group
dev` (the dev-dep declaration), non-Python repos via the dev
container image's pre-baked `standard-tooling`. The
`standards-compliance` composite action no longer clones
`standard-tooling` onto runners.

### Key Constraints

- **Portability**: Scripts must work on both macOS and Linux
- **shellcheck clean**: All bash scripts must pass shellcheck
- **No repo-specific logic**: Scripts must work in any consuming repository
