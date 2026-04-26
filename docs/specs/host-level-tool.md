# `standard-tooling` as a host-level developer tool

**Status:** Draft — pending `paad:pushback`
**Issue:** [#286](https://github.com/wphillipmoore/standard-tooling/issues/286)
**Supersedes:** `docs/specs/git-url-dev-dependency.md` (rejected 2026-04-24)
**Rejection record:**
[`paad/pushback-reviews/2026-04-24-git-url-dev-dependency-pushback.md`](../../paad/pushback-reviews/2026-04-24-git-url-dev-dependency-pushback.md)
**Author:** wphillipmoore
**Last updated:** 2026-04-24

## Purpose

Define the canonical distribution model for `standard-tooling` across
the managed fleet. The tool must be available on every active
developer's host — in any repo, in any language — without per-repo
bootstrap bespoke to each consumer.

This spec intentionally reaches across repo boundaries:
`standard-tooling-docker` and `standard-tooling-plugin` are child
repositories of `standard-tooling` (factored out for build and
deployment reasons, not because they are logically independent). This
spec dictates the distribution contract they implement.

## Problem statement

`standard-tooling` provides host-side CLI tools (`st-docker-run`,
`st-commit`, `st-submit-pr`, `st-prepare-release`, `st-validate-local`,
etc.) used across the entire fleet. It is **not** on PyPI and will not
be (first-party tooling, not a public library).

Two prior distribution approaches both failed:

1. **Sibling-checkout + `.venv-host/bin`** — assumes every consumer has
   `../standard-tooling` cloned and bootstrapped. Produced repeated
   "tool not found on PATH" failures when developers or agents forgot
   the bootstrap step. This is the failure mode that motivated
   `plugin#69`.
2. **Per-repo git-URL dev dependency via `[tool.uv.sources]`**
   (rejected 2026-04-24) — assumes every consumer has a
   `pyproject.toml`. Of the 5 non-deferred consumers, only 1 is a
   Python project. The pattern could not reach the fleet.

A further wrinkle — surfaced during #286 spec work and tracked in
[standard-tooling-docker#51](https://github.com/wphillipmoore/standard-tooling-docker/issues/51) —
is that `standard-tooling` is **also** pre-baked into the dev
container images. Today the images `git clone -b develop && uv pip
install --system` at build time, so every image carries a
point-in-time copy of `standard-tooling` that drifts from the host
version between image rebuilds. Post-merge validation has been
silently failing against stale image copies. Any new distribution
model has to treat the container image as a deployment target, not an
implementation detail.

## Decision

`standard-tooling` has **three coordinated deployment targets** with
one shared source of truth (the rolling minor tag on the
`standard-tooling` repo). All three must track that tag for the
fleet to behave consistently.

### Six principles

1. **Host-level tier.** `standard-tooling` lives on the host alongside
   `git`, `gh`, `uv`. It is on `PATH` because the developer's machine
   has it, not because any repo declares it.
2. **Host install via `uv tool install`.** Canonical mechanism across
   macOS and Linux. Puts console scripts at `~/.local/bin/` (the
   same directory `uv`'s official installer configures on `PATH`).
   `standard-tooling` is not on PyPI; install is from the GitHub git
   URL.
3. **Upgrade is manual and documented.** A one-liner run after each
   release. Shell-startup auto-detection / auto-update is **explicitly
   rejected** (invisible mutation of the dev environment is
   anti-debug).
4. **Dev-tree override via `PATH` ordering.** When testing an
   unreleased version, prepend the local checkout's venv to `PATH`
   for the shell. No framework, no flags.
5. **Python consumers MUST declare `standard-tooling` as a dev dep.**
   Pinned to the rolling minor tag via `[tool.uv.sources]`. This
   makes the project's `.venv` — not the image's pre-bake — the
   source of `st-*` inside the container, eliminating drift between
   the repo and the image. Non-Python consumers cannot declare, so
   they rely on the image's pre-bake; see principle 6.
6. **The dev container image tracks the rolling minor tag and
   rebuilds on every `standard-tooling` release.** The image's
   pre-baked `standard-tooling` is the sole `st-*` source for
   non-Python consumers, so the image cannot be allowed to drift.
   The image build pins to `v{major.minor}` (not `develop`) and
   rebuilds are triggered by `standard-tooling`'s release pipeline.

## Deployment targets

| Target | Install mechanism | Who uses it | Freshness mechanism |
|---|---|---|---|
| **Developer host** | `uv tool install` from git URL (canonical); `pip install` from git URL (alternative) | Host-side commands: `st-docker-run`, `st-commit`, `st-submit-pr`, `st-prepare-release`, `st-finalize-repo` | Manual one-liner after each release |
| **Python project `.venv`** (MUST for Python consumers) | `[tool.uv.sources]` git URL + `uv sync` | `uv run st-*` inside the container for validators: `st-validate-local`, `st-validate-local-python`, `st-markdown-standards`, etc. | `uv lock --upgrade-package standard-tooling` per repo; rolling tag means the upgrade is a no-arg re-lock |
| **Dev container image** (pre-bake) | `pip install` from git URL pinned to rolling minor tag, baked into image at build time | `st-*` inside the container for non-Python consumers (plugin, docker, docs) | Automated image rebuild on every `standard-tooling` release, pulling the current rolling tag |

These targets are coordinated, not redundant. Each covers a failure
mode the others cannot:

- Without the **host install**, `st-docker-run` cannot launch a
  container in the first place; nothing else matters.
- Without the **project `.venv` declaration**, Python consumers run
  whatever version was in the image at build time — which is exactly
  the drift problem in #51.
- Without the **image pre-bake**, non-Python consumers (plugin,
  docker, docs) have no `st-*` on PATH inside the container at all.

Consistency across the fleet means all Python consumers take the same
path (project `.venv`) and all non-Python consumers take the other
(image pre-bake). Mixing — some Python repos declare, others rely on
the image — is explicitly forbidden because it creates two debugging
surfaces where one suffices. See
[Why MUST, not SHOULD](#why-must-not-should).

## Canonical install (host)

```bash
uv tool install 'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.2'
```

`v1.2` is the rolling minor tag. `standard-actions`'
[`tag-and-release`](https://github.com/wphillipmoore/standard-actions/blob/main/actions/publish/tag-and-release/action.yml)
force-updates it on every patch release (`git tag -f v1.2 HEAD`),
so a git-URL install against `v1.2` always resolves to the latest
patch on the current minor. Bump to `v1.3` etc. when the publisher
cuts a new minor and decides consumers should opt in.

> **Note on tag schemes.** The repository carries two parallel tag
> families. Consumers only see and use the first; the second is
> internal scaffolding for the changelog flow.
>
> | Tag pattern | Where | Purpose | User-facing? |
> |---|---|---|---|
> | `v1.3.0`, `v1.3` | `main` | Release tag + rolling minor tag (the install pins target these) | Yes |
> | `develop-v1.3.0` | `develop` | Boundary marker for `git-cliff`'s changelog scoping during the next release | No |
>
> The `develop-` prefix is invisible to install / consumption; it
> only exists so `st-prepare-release` can scope the next changelog
> diff to the right starting point. Treat any `develop-v*` tag as
> internal — never pin to one.

### `uv tool install` vs `pip install`

`uv tool install` is canonical. `pip install` is a documented
alternative, not a replacement.

| | `uv tool install` (canonical) | `pip install` (alternative) |
|---|---|---|
| Install target | Isolated venv at `~/.local/share/uv/tools/standard-tooling/` | Whatever Python env `pip` runs from |
| Scripts land in | `~/.local/bin/` (the path `uv`'s official installer already configures) | `bin/` of the Python env `pip` runs from |
| Dep isolation | Fully isolated | Shared with the containing env |
| macOS system Python | Works | Works (user-owned Framework Python) |
| Linux system Python | Works | Fails without `sudo` or `--break-system-packages` (PEP 668) |
| `uv` installed standalone (no Python env) | Works | No applicable target env |
| Uninstall | `uv tool uninstall standard-tooling` | `pip uninstall standard-tooling` |

**Why `uv tool install` is canonical:**

- **Cross-platform without caveats.** Works identically on macOS
  and Linux. No `--user` vs system-wide decision, no PEP 668
  exception flags, no `sudo`.
- **Matches the `uv` installation pattern.** Developers install
  `uv` via the official installer, which configures `~/.local/bin`
  on `PATH`. `uv tool install` drops console scripts into the
  exact same directory, so `standard-tooling` scripts are on `PATH`
  automatically.
- **Zero pollution of the developer's Python environments.**
  `standard-tooling` and its transitive deps live in their own
  venv, invisible to any other Python work on the machine.
- **Self-upgrading.** `uv tool upgrade standard-tooling` is a
  shorter, tag-aware one-liner than the `pip install --upgrade`
  equivalent.

Developers or CI environments that prefer — or already have — a
`pip`-based install may use `pip install` with the same git URL,
accepting the platform caveats above. The existing primary-developer
machine, which has `standard-tooling` installed via `pip` into
Framework Python, is a valid alternative install and does not need
to migrate.

## Upgrade (host)

Run after each `standard-tooling` release:

```bash
uv tool upgrade standard-tooling
```

`uv tool upgrade` re-resolves the git reference, pulls the current
tip of the rolling minor tag (`v1.2` today), and rebuilds the
isolated venv. No need to repeat the full git URL — uv remembers
the source from the initial `uv tool install`.

For `pip install` users:

```bash
pip install --upgrade 'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.2'
```

`--upgrade` is required for `pip` to re-resolve the git reference;
without it, pip sees the package already installed and skips. The
`v1.2` pin ensures resolution picks up the latest patch on the
current minor.

### Why not auto-upgrade

Shell-startup hooks, cron jobs, or post-release auto-install were
considered and explicitly rejected:

- **Invisible mutation.** The developer's `PATH` contents changing
  without their awareness breaks reproducibility during debugging.
- **Failure mode inversion.** An auto-upgrade that partially fails
  leaves the host in a state the developer didn't initiate and
  doesn't know how to diagnose.
- **Release cadence is low-frequency.** Manual upgrade is a small
  tax paid a handful of times per year.

The release announcement (GitHub release notes) includes the upgrade
one-liner, so the action is copy-paste.

## Dev-tree override (host)

Testing an unreleased version of `standard-tooling` from a local
checkout is the **one case** where host-side venv bootstrapping
survives. This is an unusual workflow — hit only when developing
`standard-tooling` itself or running an ad-hoc host-side integration
test against pre-release code. The normal path is `uv tool install`
described above.

The override uses a dedicated host-side venv named `.venv-host`
(not `.venv`):

```bash
cd ~/dev/github/standard-tooling
UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev
export PATH="$PWD/.venv-host/bin:$PATH"      # shell-local override
which st-docker-run                           # confirms override wins
```

`PATH` ordering alone handles the override — the shell picks the
first match. Unset the `PATH` export (or open a fresh shell) to
revert to the host-installed version.

### Why `.venv-host`, not `.venv`

The `standard-tooling` repo is itself developed and validated inside
the dev container. Inside the container, `uv sync` populates `.venv/`
with shebangs pointing at the container's Python
(`/workspace/.venv/...`). Those binaries cannot run on the host — the
shebang path doesn't resolve to a host executable.

If the host override used `.venv/`, host-side `uv sync` would
overwrite the container's venv (breaking container validation) or
vice versa. Separating the two under `.venv-host/` is the structural
fix, not a workaround: host-Python and container-Python shebangs are
different interpreters, and must live in different directories.

`.venv-host` therefore survives specifically and only as the
dev-tree-override venv for this repo (and, by extension, any Python
consumer that needs to test unreleased `standard-tooling` from a
sibling checkout). It is **not** the normal install mechanism —
that remains `uv tool install` as described under
[Canonical install](#canonical-install-host).

## Python consumer dev-dep declaration (required)

Every Python consumer MUST declare `standard-tooling` as a dev dep:

```toml
# pyproject.toml
[dependency-groups]
dev = [
    "standard-tooling",
    # … other dev deps …
]

[tool.uv.sources]
standard-tooling = { git = "https://github.com/wphillipmoore/standard-tooling", tag = "v1.2" }
```

After `uv sync --group dev`, `.venv/bin/st-*` contains the pinned
version. Inside the container, `uv run st-validate-local` resolves
against `.venv/` and the image's pre-bake is not consulted.

### Why MUST, not SHOULD

Uniformity across Python repos is load-bearing. If repo A declares
the dev dep and repo B does not:

- Repo A runs the tag-pinned version from `.venv/`.
- Repo B runs the image's pre-baked copy.
- Debugging "why does validation behave differently in A vs B?"
  becomes a multi-source version-archaeology exercise.

The freshness guarantee this spec is trying to deliver —
"`st-validate-local` runs the version the pin says" — only holds
fleet-wide if every Python consumer takes the same path. Optional
adoption guarantees some repos fall off.

### Keeping lockfiles current

The rolling-minor tag means `uv lock --upgrade-package
standard-tooling` resolves to the current tip of `v1.2`. Consumers
bump their lockfile by running that command and committing `uv.lock`.

The cadence for these bumps is left to each consumer. Automation
(dependabot, scheduled refresh PRs) is desirable but out of scope
for this spec. What IS in scope: pinning to the rolling minor tag
rather than a fixed patch tag, so the bump is a no-arg re-lock and
does not require editing `pyproject.toml`.

### Non-Python consumers

Non-Python consumers (`standard-tooling-plugin`, `standard-tooling-docker`,
`the-infrastructure-mindset`, `standards-and-conventions`, and the
Ruby / Go / Rust / Java variants of `mq-rest-admin-*`) cannot
declare `standard-tooling` as a dev dep because they have no
`pyproject.toml` to declare in. They rely on the dev container
image's pre-bake; freshness is the image's responsibility (see
[Dev container image policy](#dev-container-image-policy)).

## Dev container image policy

The dev container images maintained in
[`standard-tooling-docker`](https://github.com/wphillipmoore/standard-tooling-docker)
are the distribution channel for non-Python consumers. Under this
spec, those images MUST:

1. **Pin `standard-tooling` to the rolling minor tag** at image
   build time. The current pre-bake script (`git clone -b develop &&
   uv pip install --system`) tracks develop branch tip, which drifts
   from releases. The replacement pins to the tag:

   ```dockerfile
   RUN pip install --no-cache-dir \
       'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.2'
   ```

2. **Rebuild automatically on every `standard-tooling` release.** A
   release of `standard-tooling` triggers a rebuild of the dev
   images, so the next `docker pull` of `dev-base` / `dev-python` /
   etc. contains the newly-released `standard-tooling`.

   Mechanism (owned by `standard-tooling-docker`): likely a
   `repository_dispatch` fired by `standard-tooling`'s release
   workflow, or a GitHub Actions workflow in
   `standard-tooling-docker` that watches the rolling tag. The
   exact mechanism is `standard-tooling-docker`'s call; this spec
   only requires the behavior.

This closes the loop for non-Python consumers: a new
`standard-tooling` release produces new images within the rebuild
cycle, and non-Python repos pull fresh `st-*` on next container
launch.

Implementation tracked in
[standard-tooling-docker#51](https://github.com/wphillipmoore/standard-tooling-docker/issues/51),
which this spec unblocks.

## CI install path

CI is not a separate deployment target. Every consumer's CI falls
into one of the two existing paths:

- **Python consumer CI** — uses the project `.venv` path. A workflow
  step that runs `uv sync --group dev` installs `standard-tooling`
  from the dev-dep declaration, exactly as on a developer's host.
  No separate install step.
- **Non-Python consumer CI** — uses the dev container image path.
  Workflows run inside the `dev-base` / `dev-python` / etc. image
  (either via `jobs.<name>.container:` or by invoking
  `st-docker-run` from the runner), and the image's pre-baked
  `standard-tooling` is on `PATH`. No separate install step.

Consequently: the `standards-compliance` composite action in
[`standard-actions`](https://github.com/wphillipmoore/standard-actions)
must stop cloning `standard-tooling` and adding `scripts/bin/` to
`PATH`. That path is a transitional artifact from before the
container pre-bake existed; under this spec, `standards-compliance`
either runs inside the dev container (non-Python case) or relies on
the consumer's own `uv sync --group dev` (Python case). Updating the
action is part of this spec's rollout (see
[Acceptance criteria](#acceptance-criteria)).

The same principle applies to any other `standard-actions` composite
that currently bootstraps `standard-tooling` onto the runner: if the
work can run inside the dev container, that's the canonical path; if
the consumer is Python, `uv sync --group dev` covers it. No CI
workflow should need a bespoke `uv tool install`.

## Git hooks

The pre-commit gate moves from git hook content to `st-commit`
itself, with a thin hook that enforces `st-commit` as the only legal
path to a commit.

### Decision: `st-commit` is the enforcement point; the hook is a gate

**All commit-context checks live in `st-commit`.** Branch-name
validation, protected-branch refusal, issue-number requirement, and
worktree-convention enforcement (the rules currently in
`src/standard_tooling/bin/pre_commit_hook.py`) move into
`src/standard_tooling/bin/commit.py`. `st-commit` becomes the single
source of truth for commit-time policy.

**The git hook becomes a trivial gate.** Its only job is to refuse
any `git commit` that did not go through `st-commit`. `st-commit`
sets the environment variable `ST_COMMIT_CONTEXT=1` before invoking
`git commit --file`; the hook checks for that variable and rejects
otherwise.

Every managed repo checks in the following bash gate:

```bash
# .githooks/pre-commit
#!/usr/bin/env bash
# Admit st-commit-driven commits.
if [[ "${ST_COMMIT_CONTEXT:-}" == "1" ]]; then exit 0; fi
# Admit derived-commit workflows that legitimately invoke `git commit`
# without going through st-commit (amend, rebase, cherry-pick, revert,
# merge-conflict resolution). GIT_REFLOG_ACTION is set by git itself.
case "${GIT_REFLOG_ACTION:-}" in
  amend|cherry-pick|revert|rebase*|merge*) exit 0 ;;
esac
echo "ERROR: raw 'git commit' is blocked. Use 'st-commit' instead." >&2
echo "See docs/repository-standards.md" >&2
exit 1
```

And enables it once per clone:

```bash
git config core.hooksPath .githooks
```

The gate has no dependency on the host install of
`standard-tooling`, no Python tooling, no entry-point resolution. It
is pure bash, identical in every repo in every language.

### Why this shape

- **Fleet-wide enforcement.** The gate fires for humans, agents, and
  CI alike. The plugin's existing `block-raw-git-commit` PreToolUse
  hook covers agents earlier in the loop, but the git hook is the
  backstop that catches anything the plugin does not.
- **One source of truth.** Adding, removing, or changing a
  commit-context check means editing one Python file (`commit.py`),
  not coordinating across a hook module and a wrapper.
- **Ecosystem-neutral.** Pure bash, no Python dependency. Works
  identically in the Python plugin repo, the Dockerfiles repo, the
  markdown docs repo, and every `mq-rest-admin-*` language variant.
- **Distribution-stable.** No shim that calls an entry point, so no
  failure mode where the host install is missing but the shim is
  present.

### Consequences

- **`st-pre-commit-hook` entry point is removed.** Its logic moves
  entirely into `st-commit`; the entry point itself and
  `src/standard_tooling/bin/pre_commit_hook.py` are deleted.
  `scripts/lib/git-hooks/pre-commit` (the in-repo hook file that
  execs the entry point) is also removed.
- **`st-commit` must always set `ST_COMMIT_CONTEXT=1`** before
  calling `git commit`. A unit test pinning this behavior is a
  requirement of the migration — forgetting it in a future refactor
  would break every commit fleet-wide.
- **Derived-commit workflows are admitted automatically.** The gate
  recognizes `GIT_REFLOG_ACTION` values set by `git` itself during
  `--amend`, `rebase`, `cherry-pick`, `revert`, and
  merge-conflict-resolution commits. These fire the pre-commit hook
  but should not be treated as raw `git commit -m "..."` for
  enforcement purposes. No user action required.
- **Escape hatch:** `ST_COMMIT_CONTEXT=1 git commit -m "..."` will
  pass the gate. This is deliberate — the env var is an in-band
  signal, and anyone who sets it manually accepts the cost of
  skipping `st-commit`'s content checks. Document it as the break
  glass.

### Check inventory

The five checks currently in `pre_commit_hook.py`, all moving into
`st-commit`:

1. Reject commits from detached HEAD.
2. Reject direct commits to `develop` / `release` / `main`.
3. Validate branch prefix against the repo's branching model (from
   `docs/repository-standards.md`).
4. Require issue number in `feature|bugfix|hotfix|chore/` branches.
5. Refuse feature-branch commits from the main worktree when
   `.worktrees/` exists (per worktree convention rule 3).

All five are preserved. Earlier pruning of #1 and #2 was considered
when they lived in a standalone hook module; now that they share a
file with message formatting, the cost of keeping them is trivial,
so no pruning is proposed here. Revisit in a separate issue if they
prove to be noise.

## Fail-loud enforcement

Two layers already exist; no new trip-wires are proposed here.

**Layer 1 — Agent sessions: plugin `validate-on-edit.sh`.** The
Claude Code plugin's `PostToolUse` hook for `Write`/`Edit`
dispatches validation through `st-docker-run`. On missing
`st-docker-run`, it emits a `hookSpecificOutput` with a clear
install pointer and exits 2. This covers every agent session that
has the plugin installed.

**Layer 2 — Shell-level: `command not found`.** When a human or CI
script invokes `st-docker-run` without the host install, the shell
itself fails with exit 127 and a clear error. Downstream `st-*`
tools fail immediately at the first call, with the shell-level
diagnostic pointing directly at the missing command.

These two layers together cover the realistic failure surface:

- Agent-driven editing (most of the traffic) → plugin hook catches it.
- Human or CI invocation → shell's built-in `command not found`.

A third layer — per-consumer trip-wires in each repo's task runner —
was considered and is **not** proposed. Adding bespoke "is
standard-tooling installed?" checks to each consumer duplicates what
the shell already does. If the two existing layers prove
insufficient in practice (measured against real failures, not
speculative ones), revisit in a follow-up spec.

The error message in `validate-on-edit.sh` currently points at the
sibling-checkout bootstrap guide. Updating it to reference this spec
is tracked in issue #288 (the docs + workarounds sweep), not here.

## Scope

### In-scope consumers

Every repo that currently uses any `st-*` command:

- **Python consumers** (MUST declare dev dep):
  - `ai-research-methodology`
  - `mq-rest-admin-python` (when it re-enters active development)
- **Non-Python consumers** (rely on image pre-bake):
  - `standard-tooling-plugin`
  - `standard-tooling-docker`
  - `the-infrastructure-mindset`
  - `standards-and-conventions`
  - `mq-rest-admin-ruby`, `-go`, `-rust`, `-java`, `-common`,
    `-dev-environment`, `-template` (all when the family re-enters
    active development)

**`standard-tooling` itself is a distinct case.** It doesn't (and
can't) declare itself as a dev dep in its own `pyproject.toml`;
`uv sync --group dev` inside the dev container installs the repo
editably into `/workspace/.venv/`, so `uv run st-*` resolves against
the repo's own source. The dev-dep declaration pattern applies to
*other* Python consumers; for this repo, the self-hosting is a
consequence of the package itself.

### Out-of-scope

- **Publishing `standard-tooling` to PyPI.** Explicitly rejected.
- **The specific automation mechanism for image rebuild-on-release.**
  `repository_dispatch`, scheduled polling, or another pattern — all
  are acceptable; the spec only requires the behavior. Mechanism
  chosen in `standard-tooling-docker#51`.
- **Automation of consumer lockfile bumps.** Manual
  `uv lock --upgrade-package standard-tooling` is the baseline; any
  dependabot / renovate / scheduled-PR layer is separate work.
- **Bash validators under `scripts/bin/`.** That directory
  (referenced in legacy `CLAUDE.md` text) no longer exists — all
  validation has migrated to Python entry points that ship via the
  host install and container pre-bake.
- **Bundled bash scripts under `scripts/lib/`.** Only `git-hooks/`
  needs consumer access, and the shim approach above covers it.

## Migration per consumer

See issue #288 for the full rollout checklist. At spec level, each
consumer's migration has these steps:

### `standard-tooling` itself (this spec's code work, before fleet rollout)

1. Move the five branch/context checks from
   `src/standard_tooling/bin/pre_commit_hook.py` into
   `src/standard_tooling/bin/commit.py`.
2. Have `st-commit` set `ST_COMMIT_CONTEXT=1` in the environment
   before invoking `git commit --file`. Add a unit test pinning
   this behavior.
3. Delete `src/standard_tooling/bin/pre_commit_hook.py`, remove the
   `st-pre-commit-hook` entry point from `pyproject.toml`, and
   delete `scripts/lib/git-hooks/pre-commit`.
4. Ship this repo's own `.githooks/pre-commit` as the
   env-var-plus-GIT_REFLOG_ACTION gate.

### Python consumers

1. Add `standard-tooling` to `[dependency-groups].dev` and declare
   the git-URL source in `[tool.uv.sources]` (snippet in
   [Python consumer dev-dep declaration](#python-consumer-dev-dep-declaration-required)).
2. Run `uv sync --group dev`; commit `pyproject.toml` + `uv.lock`.
3. Replace any existing `core.hooksPath` setting and hook file with
   the new `.githooks/pre-commit` env-var gate.
4. Remove sibling-checkout and PATH-hack references from docs,
   bootstrap scripts, and CI. (`.venv-host` is retained only in
   `standard-tooling` itself for the dev-tree-override case; it
   should not appear in any other consumer.)
5. Verify: `st-docker-run -- uv run st-validate-local` works in a
   fresh clone after `uv sync --group dev`; raw `git commit` is
   refused with the gate's error.

### Non-Python consumers

1. Replace any existing `core.hooksPath` setting and hook file with
   the new `.githooks/pre-commit` env-var gate.
2. Remove sibling-checkout and PATH-hack references from docs,
   bootstrap scripts, and CI. (Non-Python consumers have no legit
   reason to hold a `.venv-host`; it belongs only to
   `standard-tooling` itself.)
3. Verify: host-installed `st-*` is on PATH; the image's pre-baked
   `st-*` is what runs inside the container; raw `git commit` is
   refused with the gate's error.

### `standard-tooling-docker` (child repo, this spec's work)

1. Replace `git clone -b develop && uv pip install --system` with
   `pip install 'standard-tooling @ git+…@v1.2'` in the common
   fragment.
2. Wire release-triggered rebuilds per
   [`standard-tooling-docker#51`](https://github.com/wphillipmoore/standard-tooling-docker/issues/51).
3. Remove the `/opt/standard-tooling/.venv/` layout if still present
   (it predates uv's system-wide install pattern).

## First-time developer setup

The canonical onboarding flow for a new developer on a new machine:

```bash
# 1. Install uv (if not already present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install standard-tooling
uv tool install 'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.2'

# 3. Confirm (~/.local/bin is already on PATH via uv's installer)
which st-docker-run
st-docker-run --help

# 4. For each repo cloned:
cd ~/dev/github/<repo>
git config core.hooksPath .githooks
uv sync --group dev       # only for Python repos
```

No sibling checkout. No `.venv-host` bootstrap. No custom install
path.

## Tradeoffs captured

### Rolling-tag pin vs. fixed-tag pin

- **Rolling `v1.2`** (chosen, all three deployment targets): patches
  flow forward on the next manual action (upgrade / re-lock /
  rebuild). A broken patch affects every consumer on that minor —
  but `standard-tooling`'s release gates and the deliberate
  non-automatic propagation mean the blast radius is one action at
  a time.
- **Fixed `v1.2.2`**: never floats. Every patch requires explicit
  action at every deployment target. Rejected for friction.

### Major-version bumps

The rolling tag is `v{major.minor}` (`v1.2`), not `v{major}` — there
is no rolling `v1` or `v2` tag. When `standard-tooling` cuts `v2.0`,
nothing at the three deployment targets moves automatically: the
developer host's `uv tool install ...@v1.2` keeps resolving against
`v1.2`; Python consumers' `pyproject.toml` pin keeps them on `v1.2`;
the dev container image's Dockerfile pin keeps pre-baking `v1.2`.
Crossing a major boundary is a deliberate, explicit edit at each
target (bump `v1.2` → `v2.0` in the consumer's `pyproject.toml`,
the image's Dockerfile, and the developer's `uv tool install`
command). This is the point: major bumps are gated, not broadcast.

### `uv tool install` vs `pip install`

Covered in [Canonical install](#canonical-install-host).

### Host install vs devcontainer-only

A pure devcontainer model ("never install `standard-tooling` on the
host") was considered and rejected:

- `st-docker-run` is the host → container bridge. It has to exist
  on the host to launch the container.
- Git hooks fire on the host, not inside the container.
- Interactive `st-commit` / `st-submit-pr` flows need host-side
  `gh` authentication.

The canonical `uv tool install` path satisfies this by keeping
`standard-tooling` in its own isolated venv — the host still has
Python, but no shared state between `standard-tooling` and any
other Python project on the machine.

### Uniform requirement for Python consumers

Covered in [Why MUST, not SHOULD](#why-must-not-should). The
consistency cost of optional adoption exceeds the per-repo cost of
a two-line `pyproject.toml` addition and a lockfile bump.

### Lockfile-bump overhead

Every patch of `standard-tooling` requires Python consumers to run
`uv lock --upgrade-package standard-tooling` and commit the
lockfile to pick up the patch inside the container. This is the
same concern pushback item #4 raised against the prior spec; it
remains a real cost but is mitigated here because:

- The rolling-minor pin means the re-lock is a no-arg command
  (no `pyproject.toml` editing, no version picking).
- The cost is per-repo-per-release, not per-repo-per-commit.
- The payoff (deterministic `.venv/bin/` contents inside the
  container, no silent drift against a stale image) is directly
  load-bearing.
- Automation (dependabot etc.) is the obvious follow-up if the
  manual cadence becomes a friction point.

### Image rebuild cadence

The spec requires release-triggered image rebuilds, but there is
always *some* window between `standard-tooling` tagging a release
and the image being rebuilt and pushed. During that window,
non-Python consumers pulling a fresh container get the
previous-release image. Mitigations:

- The window is minutes-to-hours for CI-driven rebuilds, not days.
- Non-Python consumers are docs / plugin / Dockerfiles repos where
  the consequence of running a one-release-behind validator is
  usually trivial.
- Python consumers (the majority of active code) are insulated from
  this window entirely via the project `.venv` path.

## Acceptance criteria

- [ ] This spec lands; `paad:pushback` run and findings addressed.
- [ ] `docs/specs/git-url-dev-dependency.md` deleted (the pushback
      report preserves the rejection record).
- [ ] `CLAUDE.md` and every file under `docs/` updated to match
      this spec. Specifically: the Consumption Model and Host
      bootstrap sections rewritten; all `scripts/lib/git-hooks`
      references replaced with `.githooks` + the env-var-plus-
      GIT_REFLOG_ACTION gate; all sibling-checkout
      (`../standard-tooling/scripts/lib/git-hooks`,
      `../standard-tooling/.venv-host/bin`) references removed;
      the worktree-convention block's hook-enforcement mention
      updated to the new gate. Greps to verify nothing remains:
      `grep -r "scripts/lib/git-hooks\|\.venv-host/bin\|\.\./standard-tooling/" CLAUDE.md docs/`.
      (Tracked in #288.)
- [ ] Getting-started docs updated to the four-step flow in
      [First-time developer setup](#first-time-developer-setup).
      (Tracked in #288.)
- [ ] Each Python consumer has `standard-tooling` declared as a
      dev dep via `[tool.uv.sources]` on the rolling minor tag.
      (Tracked in #288.)
- [ ] Five pre-commit checks moved from `pre_commit_hook.py` into
      `commit.py`; `st-commit` sets `ST_COMMIT_CONTEXT=1`;
      `st-pre-commit-hook` entry point and its source file
      deleted. (Code change in this repo, not #288.)
- [ ] Each in-scope consumer has the `.githooks/pre-commit`
      env-var gate checked in and `.venv-host` / sibling-checkout
      references removed. (Tracked in #288.)
- [ ] Plugin `validate-on-edit.sh` error message updated to point
      at this spec. (Tracked in #288.)
- [ ] `standard-tooling-docker` image build pins to the rolling
      minor tag. (Tracked in
      [standard-tooling-docker#51](https://github.com/wphillipmoore/standard-tooling-docker/issues/51).)
- [ ] `standard-tooling-docker` rebuilds automatically on every
      `standard-tooling` release. (Tracked in
      [standard-tooling-docker#51](https://github.com/wphillipmoore/standard-tooling-docker/issues/51).)
- [ ] `standards-compliance` (and any other `standard-actions`
      composite that clones `standard-tooling` or puts
      `scripts/bin/` on `PATH`) is updated to rely on the Python
      `uv sync --group dev` path or the dev container image
      pre-bake. (Tracked in a new `standard-actions` issue to be
      filed under #288.)

## References

- Rolling-tag behavior:
  [`standard-actions` `tag-and-release`](https://github.com/wphillipmoore/standard-actions/blob/main/actions/publish/tag-and-release/action.yml)
- `pip install` from VCS:
  <https://pip.pypa.io/en/stable/topics/vcs-support/>
- `uv tool install`:
  <https://docs.astral.sh/uv/guides/tools/#installing-tools>
- uv sources (git URL + tag):
  <https://docs.astral.sh/uv/concepts/projects/dependencies/#git>
- Git `core.hooksPath`:
  <https://git-scm.com/docs/githooks#_description>
- Rejected predecessor:
  [`docs/specs/git-url-dev-dependency.md`](git-url-dev-dependency.md)
  and
  [pushback report](../../paad/pushback-reviews/2026-04-24-git-url-dev-dependency-pushback.md)
- Image-staleness context:
  [standard-tooling-docker#51](https://github.com/wphillipmoore/standard-tooling-docker/issues/51)
