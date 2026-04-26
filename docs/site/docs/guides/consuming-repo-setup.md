# Consuming Repo Setup

This is the full walkthrough for onboarding a new repository to use
standard-tooling. For the one-screen quickstart, see
[Getting Started](../getting-started.md). For how the workflow
unfolds once you're set up, see [Git Workflow](git-workflow.md).

## Mental model — what you're installing

Standard-tooling is delivered through three coordinated surfaces.
The setup steps below wire up each one:

| Surface | What it is | How you consume it |
|---|---|---|
| **Host bridge** | A single host-side CLI tool, `st-docker-run`, that runs commands inside a dev container image. | `uv sync` into `.venv-host`; add its `bin/` to PATH. |
| **Dev container** | `ghcr.io/wphillipmoore/dev-<lang>:<version>` — pre-baked images with language runtimes, validators, and every other `st-*` tool installed. | Pulled automatically by `st-docker-run`; nothing to install manually. |
| **Claude Code plugin** | `standard-tooling-plugin` — hooks, skills, agents, and slash commands that enforce the workflow at the Claude-Code-tool level. | Declared in `.claude/settings.json`; Claude Code loads on session start. |

Plus two scripted layers that aren't installed as packages but are
expected to be present in every consuming repo:

- **Local git hooks** — `scripts/lib/git-hooks/pre-commit` from
  standard-tooling, wired via `git config core.hooksPath`.
- **CI workflow** — the `standards-compliance` composite action
  from `wphillipmoore/standard-actions`, invoked from your repo's
  `.github/workflows/ci.yml`.

Both of these validate the repo profile and enforce branching rules
from two different entry points. See
[Git Workflow → Two enforcement layers](git-workflow.md#two-enforcement-layers)
for how they fit together.

## Step 1: Host prerequisites

Install on your host (macOS or Linux):

**Docker** — the container engine. Docker Desktop on macOS is fine;
Docker Engine on Linux works too.

**uv** — Python package manager. Used to bootstrap the host venv and
(inside the container) to manage Python dependencies. Install via
the [official installer](https://docs.astral.sh/uv/getting-started/installation/).

**gh** — GitHub CLI. Must be authenticated
(`gh auth login`). Used by `st-submit-pr` to create PRs and, inside
the container, to pass through your GitHub token for push operations.

**Git and Bash** — ship with macOS by default and are standard on
Linux.

You do **not** need to install language runtimes, linters, test
frameworks, markdownlint, shellcheck, or any `st-*` tool other than
`st-docker-run` on the host. All of those live inside the container.

## Step 2: Clone and bootstrap standard-tooling

Clone standard-tooling as a sibling directory. The exact location
doesn't matter much — just make sure you can reference it with a
consistent relative path from your consuming repo.

```bash
cd ~/dev/github   # or wherever
git clone https://github.com/wphillipmoore/standard-tooling.git
```

Bootstrap the host venv:

```bash
cd standard-tooling
UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev
```

!!! important "Why `UV_PROJECT_ENVIRONMENT=.venv-host`"
    The project also uses a `.venv` inside the dev container (at
    `/workspace/.venv/`). Running a plain `uv sync` on the host
    would create that container-venv on your host filesystem, with
    shebangs pointing at `/workspace/.venv/bin/python` — which
    doesn't exist on your host, making every `st-*` entry point
    unrunnable. Setting `UV_PROJECT_ENVIRONMENT=.venv-host` creates
    a separate host-specific venv with the correct host-Python
    shebangs, and `--group dev` pulls the dependencies
    `st-docker-run` needs.

This creates `.venv-host/bin/` with `st-docker-run` and a handful of
other host-side scripts.

## Step 3: PATH configuration

Add two directories to your PATH:

```bash
export PATH="$HOME/dev/github/standard-tooling/.venv-host/bin:$HOME/dev/github/standard-tooling/scripts/bin:$PATH"
```

- `.venv-host/bin/` — the Python-packaged host entry points,
  including `st-docker-run`.
- `scripts/bin/` — grandfathered bash validators consumed via PATH.
  Most still have `st-*` Python equivalents, but some CI paths
  still reach for the bash versions.

Add this to `~/.bashrc`, `~/.zshrc`, or your shell's equivalent so
it persists.

Optional — add `gh`'s token to your environment so it flows into
the container automatically on `st-docker-run` invocations:

```bash
export GH_TOKEN=$(gh auth token)
```

## Step 4: Git hook setup

From your consuming repo's root:

```bash
git config core.hooksPath ../standard-tooling/scripts/lib/git-hooks
```

Adjust the relative path if standard-tooling lives somewhere other
than the parent directory. This must be re-run per fresh clone —
it lives in `.git/config`, which isn't versioned.

The pre-commit hook enforces:

- Detached-HEAD commits blocked
- Direct commits to protected branches (`develop`/`release`/`main`)
  blocked
- Branch names must use one of the allowed prefixes for the repo's
  `branching_model`
- Work branches (`feature/*`, `bugfix/*`, `hotfix/*`, `chore/*`)
  must include a repository issue number

Full reference: [Git Hooks and Validation][hooks-doc].

## Step 5: Repository profile

Create `docs/repository-standards.md` at your repo root. This is
the primary configuration surface for the validators:

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

Required attributes and accepted values:

| Attribute | Values | Notes |
|---|---|---|
| `repository_type` | `application`, `library`, `tooling`, `documentation` | Informational; some validators branch on this. |
| `versioning_scheme` | `semver`, `calver`, `none` | How releases are versioned. |
| `branching_model` | `library-release`, `application-promotion`, `docs-single-branch` | Determines which branch prefixes the pre-commit hook allows. |
| `release_model` | `tagged-release`, `continuous-deploy`, `none` | Affects release-flow tooling expectations. |
| `supported_release_lines` | integer (commonly `1`) | How many concurrent major lines you support. |
| `primary_language` | `python`, `go`, `java`, `rust`, `ruby`, `shell`, `none` | Determines which per-language validators run. |

The `AI co-authors` section defines which `Co-Authored-By` trailer
values `st-commit` accepts for `--agent`. Add one line per accepted
agent identity.

Values containing `<`, `>`, or `|` are rejected as placeholders by
`st-repo-profile`.

## Step 6: Enable the Claude Code plugin

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

Commit this file. It's part of your repo's reproducible
environment — any Claude Code session opened in this repo will
pick up the plugin via this declaration.

What the plugin provides:

- **PreToolUse hooks** on `Bash` that block raw `git commit`, raw
  `gh pr create`, heredoc syntax, and (on repos that have adopted
  the worktree convention) commits originating outside
  `.worktrees/<name>/`.
- **PostToolUse hooks** that remind you to run `st-finalize-repo`
  after `st-submit-pr`, and that surface deprecation warnings in
  test output.
- **Stop hooks** that prevent session exit if a PR was submitted
  but never finalized.

See the plugin's own
[Hooks reference](https://github.com/wphillipmoore/standard-tooling-plugin/blob/develop/docs/site/docs/hooks/index.md)
for the full list.

!!! warning "Plugin install is a known rough edge"
    The plugin itself has not yet been cut as a proper versioned
    release; Claude Code consumes it directly from the repo's
    default branch. Updates can be slow to propagate and the local
    `~/.claude/plugins/marketplaces/` and `…/cache/` directories
    sometimes need manual refreshing. All tracked in
    [standard-tooling-plugin#46](https://github.com/wphillipmoore/standard-tooling-plugin/issues/46).
    The settings above are enough to get going; plan on
    occasionally running `git pull` in
    `~/.claude/plugins/marketplaces/standard-tooling-marketplace/`
    if a hook seems outdated.

## Step 7: Worktree convention

Every managed repo adopts the worktree convention so multiple
Claude Code agents can work in parallel without colliding. Two
tiny changes:

Add `.worktrees/` to your `.gitignore`:

```bash
echo '.worktrees/' >> .gitignore
```

Add a `## Parallel AI agent development` section to your
`CLAUDE.md`. Every managed repo has one you can copy — they differ
only in the repo name and example issue number. The canonical text
lives in the worktree convention spec at
`docs/specs/worktree-convention.md` in standard-tooling; a short
local section in each repo's CLAUDE.md is the on-ramp, and the
plugin's commit-block hook activates against the presence of
`.worktrees/` in `.gitignore`.

For how to actually use worktrees during development, see
[Git Workflow → Parallel work with worktrees](git-workflow.md#parallel-work-with-worktrees).

## Step 8: Markdownlint configuration

Create `.markdownlint.yaml` at your repo root:

```yaml
default: true
no-duplicate-heading:
  siblings_only: true
# Exempt tables and code blocks from the 80-char line-length check.
# Wide reference tables and pasted commands legitimately exceed it.
MD013:
  line_length: 80
  tables: false
  code_blocks: false
# Disable the table-column-style rule. Tables render correctly
# regardless of strict pipe alignment; enforcing it adds maintenance
# burden for no reader benefit.
MD060: false
```

The base rule set (`default: true`) plus the three customizations
above match what standard-tooling itself uses, so markdown files
that pass locally will pass in CI.

Optional: add `.markdownlintignore` to skip generated files:

```text
CHANGELOG.md
releases/
```

## Step 9: CI workflow

Use the `standards-compliance` composite action from
`wphillipmoore/standard-actions`. Minimal workflow
(`.github/workflows/ci.yml`):

```yaml
name: CI

on:
  pull_request:

permissions:
  contents: read

jobs:
  standards-compliance:
    name: "ci: standards-compliance"
    runs-on: ubuntu-latest
    container: ghcr.io/wphillipmoore/dev-base:latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v6

      - name: Validate standards
        uses: wphillipmoore/standard-actions/actions/standards-compliance@develop
```

What the composite action runs inside the `dev-base` container:

- `st-repo-profile` — validates `docs/repository-standards.md`
- `st-markdown-standards` — markdownlint + structural checks
- `st-pr-issue-linkage` — validates PR body has an issue linkage
  keyword (`Fixes`, `Closes`, `Resolves`, `Ref`)

The `dev-base` container already has standard-tooling on PATH, so
no further setup is needed in the workflow.

See the [Three-Tier CI](three-tier-ci.md) guide if you also want
per-language test/lint/audit tiers.

## Step 10: Verify end-to-end

Once the above is in place, sanity-check each layer:

```bash
# 1. Host bridge — should print st-docker-run help
st-docker-run --help

# 2. Dev container — pulls an image on first run and runs a
#    tiny command inside it
st-docker-run -- echo "container ok"

# 3. Repo profile — runs st-repo-profile inside the container
st-docker-run -- uv run st-repo-profile

# 4. Git hook — creating a bad branch name and trying to commit
#    should be blocked
git checkout -b bad-name
git commit --allow-empty -m "test"     # expected: blocked
git checkout -
git branch -D bad-name

# 5. Plugin hook (requires Claude Code session) — in a Claude
#    Code session in this repo, have Claude try to run a raw
#    `git commit`. The plugin should block it and point at
#    st-commit.
```

If any step fails, check the corresponding section above, then
re-run. Common causes: PATH missing an entry, `.venv-host` built
without the `UV_PROJECT_ENVIRONMENT` override, `.claude/settings.json`
not committed to the branch your Claude Code session loaded.

## Keeping up to date

Standard-tooling's host side is consumed via the sibling
`.venv-host/` checkout. To pull updates:

```bash
cd ../standard-tooling
git pull
UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev
```

!!! important "Don't drop the `UV_PROJECT_ENVIRONMENT` override"
    It applies on every sync, not just the initial bootstrap. A
    plain `uv sync` in the standard-tooling checkout will rebuild
    `.venv-host/` with the wrong shebangs again.

The dev container images auto-update on `st-docker-run` pulls — the
tag is a minor version (`3.12`, `1.26`, etc.) that tracks upstream
releases. If you need a fresh image, `docker pull
ghcr.io/wphillipmoore/dev-<lang>:<version>` forces a refresh.

The Claude Code plugin can be stale after a release; manual
refresh:

```bash
git -C ~/.claude/plugins/marketplaces/standard-tooling-marketplace pull
# then restart Claude Code
```

## Troubleshooting

- **`st-docker-run: command not found`** — `.venv-host/bin` isn't
  on PATH, or the `UV_PROJECT_ENVIRONMENT` override was skipped
  when bootstrapping.
- **`st-*` commands fail with shebang errors** — `.venv-host/` was
  built with a plain `uv sync` (no `UV_PROJECT_ENVIRONMENT=.venv-host`).
  Remove the venv and re-bootstrap.
- **`manifest unknown` when pulling a container image** — the tag
  you're asking for doesn't exist on GHCR. Older docs referenced
  `ghcr.io/wphillipmoore/dev-docs:latest` (renamed to `dev-base` in
  standard-tooling#252); make sure your workflow files use the new
  name.
- **Plugin hooks don't fire** — check that `.claude/settings.json`
  is present, committed, and syntactically valid JSON. Restart
  Claude Code; the plugin is loaded at session start. If still
  stuck, refresh the local plugin marketplace clone per "Keeping
  up to date" above.
- **Commits blocked with "originate from inside .worktrees/"** —
  intentional. This repo has adopted the worktree convention.
  Create a worktree for your work; see
  [Git Workflow → Parallel work with worktrees](git-workflow.md#parallel-work-with-worktrees).
- **`st-submit-pr` threw a `CalledProcessError` on auto-merge** —
  expected since 2026-04-22. Auto-merge is disabled org-wide; the
  PR itself was created successfully. Tracked in
  [standard-tooling#268](https://github.com/wphillipmoore/standard-tooling/issues/268).

For a broader troubleshooting index see
[Git Workflow → Troubleshooting](git-workflow.md#troubleshooting).

## Related

- [Git Workflow](git-workflow.md) — how the per-change cycle
  actually unfolds once setup is done
- [Git Hooks and Validation][hooks-doc] —
  pre-commit hook + validator reference
- [Three-Tier CI](three-tier-ci.md) — per-language test/lint/audit
  tier wiring
- [Releasing](releasing.md) — release workflow
- [Worktree convention spec][worktree-spec]
  — canonical reference for the parallel-agent convention

[hooks-doc]: https://github.com/wphillipmoore/standard-tooling/blob/develop/docs/git-hooks-and-validation.md
[worktree-spec]: https://github.com/wphillipmoore/standard-tooling/blob/develop/docs/specs/worktree-convention.md
