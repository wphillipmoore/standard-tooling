# Getting Started

A five-to-ten minute quickstart for wiring up a new repository to
use standard-tooling. For the detailed walkthrough with rationale,
CI config, and troubleshooting, see
[Consuming Repo Setup](guides/consuming-repo-setup.md).

## Prerequisites

Install these on your host:

- **Docker** — the dev container engine
- **uv** — Python package manager
  ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **`gh` CLI** — GitHub CLI, authenticated
  (`gh auth login`)
- **macOS or Linux** (Bash)

Everything else — language runtimes, linters, test frameworks, all
but one of the `st-*` tools — lives inside the dev container. The
only `st-*` tool that runs on the host is `st-docker-run`, which
bridges into the container.

## 1. Clone standard-tooling as a sibling

```bash
cd ~/dev/github   # or wherever you keep your repos
git clone https://github.com/wphillipmoore/standard-tooling.git
```

## 2. Bootstrap the host venv

```bash
cd standard-tooling
UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev
```

!!! important "The `UV_PROJECT_ENVIRONMENT` override matters"
    Without it, `uv sync` creates a `.venv` with container-path
    shebangs (`/workspace/.venv/...`) that don't work on the host.
    The `.venv-host` name and the `--group dev` dependencies are
    both required.

This installs `st-docker-run` and the other host-side entry points
into `.venv-host/bin/`.

## 3. Put host tools on PATH

```bash
export PATH="$HOME/dev/github/standard-tooling/.venv-host/bin:$HOME/dev/github/standard-tooling/scripts/bin:$PATH"
```

Add this to your shell profile so it persists across sessions.

## 4. Configure git hooks in your consuming repo

From your repo:

```bash
git config core.hooksPath ../standard-tooling/scripts/lib/git-hooks
```

This must be re-run once per fresh clone; it's not persisted.

## 5. Enable the Claude Code plugin

Create `.claude/settings.json` in your repo:

```json
{
  "extraKnownMarketplaces": {
    "standard-tooling-marketplace": {
      "source": {
        "source": "github",
        "repo": "wphillipmoore/standard-tooling-plugin"
      }
    }
  },
  "enabledPlugins": {
    "standard-tooling@standard-tooling-marketplace": true
  }
}
```

Commit this file — it's part of the repo's reproducible setup.

!!! note "Plugin install is a known rough edge"
    The install/update flow for the plugin itself is tracked in
    [standard-tooling-plugin#46](https://github.com/wphillipmoore/standard-tooling-plugin/issues/46).
    For now, this settings.json entry is enough for Claude Code to
    discover and enable the plugin on the next session restart.

## 6. Create your repository profile

Create `docs/repository-standards.md` with the six required
attributes (and AI co-author entries if you'll use them):

```markdown
# Repository Standards

## Table of Contents

- [AI co-authors](#ai-co-authors)
- [Repository profile](#repository-profile)

## AI co-authors

- Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>

## Repository profile

- repository_type: library
- versioning_scheme: semver
- branching_model: library-release
- release_model: tagged-release
- supported_release_lines: 1
- primary_language: python
```

Pick the values that match your repo. See
[Consuming Repo Setup](guides/consuming-repo-setup.md) for the full
attribute reference.

## 7. Adopt the worktree convention

Add `.worktrees/` to your `.gitignore`:

```bash
echo '.worktrees/' >> .gitignore
```

Add a "Parallel AI agent development" section to your `CLAUDE.md`
describing the convention. Every managed repo already has one you
can copy from; the canonical source is
[the worktree convention spec](../specs/worktree-convention.md).

## 8. Verify

```bash
# Host tooling reachable
st-docker-run --help

# Repo profile validates (runs inside the container)
st-docker-run -- uv run st-repo-profile

# Git hook fires on a misnamed branch
git checkout -b bad-branch-name
git commit --allow-empty -m "test"    # should be blocked by the hook
git checkout -
git branch -D bad-branch-name
```

If all three steps behave as expected, you're wired up correctly.

## Next steps

- **[Consuming Repo Setup](guides/consuming-repo-setup.md)** —
  detailed walkthrough including CI workflow, markdownlint config,
  plugin nuances, and troubleshooting.
- **[Git Workflow](guides/git-workflow.md)** — branching, commit /
  PR / finalize cycle, two-layer enforcement, worktrees in practice.
- **[Worktree convention spec](../specs/worktree-convention.md)**
  — full rationale for the parallel-agent convention, failure
  modes, memory-path implications.
