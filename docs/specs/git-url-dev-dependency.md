# Git-URL dev-dependency convention

## Context

`standard-tooling` provides host-side CLI tools (`st-docker-run`,
`st-commit`, `st-submit-pr`, `st-prepare-release`,
`st-merge-when-green`, `st-finalize-repo`, etc.) that every
managed repository needs during local development.

Today those tools are made available through a **sibling-checkout
convention**: consuming repos assume `standard-tooling` is cloned
in `../standard-tooling` with a `.venv-host/bin/` populated. Each
consumer either hard-codes that path or expects the user to add
it to `PATH` manually. This has caused repeated "tool not found
on PATH" failures across sessions — validator hooks, publish
scripts, and CI-style workflows all break when the host venv
isn't set up exactly as assumed.

`standard-tooling` is **not** published to PyPI and will not be
(by design — it's first-party tooling for this ecosystem, not a
public library). So the normal "add it to `[dependency-groups].dev`
and let PyPI resolve it" path isn't available.

## Decision

Every managed consumer repository declares `standard-tooling` as a
**git-URL dev dependency**, using `uv`'s native sources mechanism.
The dep is pinned to a **rolling major.minor tag** so patch
releases cascade automatically without bump PRs in every repo.

## Canonical pattern

In a consuming repository's `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "standard-tooling",
    # ... other dev deps
]

[tool.uv.sources]
standard-tooling = { git = "https://github.com/wphillipmoore/standard-tooling", tag = "v1.3" }
```

Tag semantics:

- `v1.3` is the **rolling minor tag** that `standard-actions`'
  `tag-and-release` composite maintains. Each patch release of
  `standard-tooling` (e.g. `v1.3.0` → `v1.3.1`) force-moves `v1.3`
  forward.
- Consumers running `uv sync --group dev` pull the current tip of
  `v1.3`. On a plain `uv sync`, tags are re-resolved each run, so
  new patches reach consumers on next sync.
- Pin to `v1.4` etc. when the publisher (you) decides consumers
  should opt in to a new minor.

After sync, the venv under the consuming repo has:

```text
.venv/bin/st-docker-run
.venv/bin/st-commit
.venv/bin/st-submit-pr
...
```

The "is it on PATH?" problem disappears — activating the venv
(or running `uv run <tool>`) finds the tools automatically.

## Scope

### In-scope (to be converted)

All consuming managed repositories that currently rely on the
sibling-checkout model:

- `ai-research-methodology` (pilot — convert first)
- `standard-tooling-plugin`
- `standard-tooling-docker`
- `infrastructure-mindset`
- `standards-and-conventions` (if it uses any `st-*` tool)
- All `mq-rest-admin-*` repos (defer until those repos re-enter
  active development)

### Out-of-scope

- `standard-tooling` itself. It's the source repo; no need to
  declare itself as a dep.

## Migration checklist per repo

For each consuming repo:

1. **Determine current reliance**. Confirm the repo uses at least
   one `st-*` CLI tool.
2. **Declare the dep**. Add to `pyproject.toml`:

   ```toml
   [dependency-groups]
   dev = [
       "standard-tooling",
   ]

   [tool.uv.sources]
   standard-tooling = { git = "https://github.com/wphillipmoore/standard-tooling", tag = "v1.3" }
   ```

   (Use the current rolling-minor tag — `v1.3` at time of writing.)

3. **Regenerate lockfile**. `uv lock`. The lockfile will record the
   commit SHA the tag currently points at, so CI gets a
   reproducible build even though the tag moves over time.
4. **Remove sibling-checkout hacks**. Anywhere the repo explicitly
   prepends `.venv-host/bin` to `PATH`, or assumes
   `../standard-tooling/.venv-host/bin/st-docker-run` exists, drop
   it. The consumer's own `.venv/bin/` now has the tools.
5. **Update CI**. CI workflows that ran `uv sync --group dev` get
   `st-*` tools for free. Remove any CI steps that checked out
   `standard-tooling` separately or added it to PATH.
6. **Update documentation**. CLAUDE.md and onboarding docs stop
   saying "clone standard-tooling as a sibling" and start saying
   "run `uv sync --group dev`."
7. **Verify**: `uv run st-docker-run --help` works from a fresh
   clone with only `uv sync --group dev` run beforehand.

## Tradeoffs captured

### Rolling-tag pin vs. fixed-tag pin

- **Rolling `v1.3`** (chosen): patches flow to consumers
  automatically on next sync. Tradeoff: a breaking patch in
  `standard-tooling` can break every consumer without a dep-bump
  PR in each repo. Mitigated by `standard-tooling`'s release
  gates and the `uv.lock` pin on a specific SHA (lockfile pinning
  means CI won't silently float until someone runs `uv lock`
  again).
- **Fixed `v1.3.0`**: consumers never float; explicit bumps only.
  Tradeoff: every patch requires N bump PRs across the fleet.
  Rejected for this reason.

### Git URL vs. local editable path

- **Git URL** (chosen as the canonical pattern): works from any
  machine, in CI, for new contributors. No local filesystem
  coupling.
- **Local editable `{ path = "../standard-tooling", editable = true }`**:
  useful when actively developing `standard-tooling` and a
  consumer simultaneously. Individual developers MAY override
  locally via a gitignored `uv.toml`:

  ```toml
  # uv.toml (gitignored)
  [sources]
  standard-tooling = { path = "../standard-tooling", editable = true }
  ```

  This overrides `pyproject.toml`'s source without affecting other
  contributors or CI.

### Network dependency at sync time

- First `uv sync` in a clean checkout requires network access to
  clone the git source. Subsequent syncs use uv's local cache.
- Air-gapped CI environments need pre-warmed caches. Not currently
  a concern for this fleet.

### What about `standard-tooling` itself updating?

- `standard-tooling`'s release pipeline already maintains the
  rolling `v1.3` tag via `tag-and-release`. No changes needed
  there.
- Consumers running `uv sync` without `--refresh` use the cached
  SHA from their `uv.lock`. When a consumer wants the latest
  patch, `uv lock --upgrade-package standard-tooling` refreshes
  just that dep.

## Relationship to existing plugin + docker infrastructure

This convention **does not replace** any of:

- The Claude Code plugin (`standard-tooling-plugin`) — plugins
  deliver hooks/skills into Claude Code sessions; that remains
  its own distribution channel.
- The dev container images — containers still run everything else
  inside them; `standard-tooling` is only needed on the HOST for
  tools like `st-docker-run` that bridge host → container.

It **does replace** the sibling-checkout convention for
host-available CLIs.

## Rollout plan (tracked in a separate umbrella issue)

1. Pilot: `ai-research-methodology`. Convert, verify, merge.
2. Cascade: the remaining in-scope repos.
3. Remove sibling-checkout documentation from CLAUDE.md and
   consuming-repo-setup guides.
4. File tracking issues in the deferred `mq-rest-admin-*` repos
   so they pick this up when they re-enter active work.

## Acceptance criteria

For each converted repo:

- [ ] `pyproject.toml` declares `standard-tooling` as a dev dep
      via `[tool.uv.sources]` with git URL + rolling-minor tag.
- [ ] `uv sync --group dev` in a fresh clone yields a venv that
      contains `st-docker-run` (and other `st-*` tools the repo
      uses).
- [ ] No lingering `PATH="$(pwd)/../standard-tooling/.venv-host/bin"`
      hacks remain in the repo.
- [ ] CI workflows do not separately clone `standard-tooling`.
- [ ] CLAUDE.md / onboarding docs updated.
- [ ] `uv.lock` is committed and pins a specific SHA.

## References

- uv sources documentation:
  <https://docs.astral.sh/uv/concepts/projects/dependencies/#git>
- uv workspace / per-developer override mechanics:
  <https://docs.astral.sh/uv/reference/settings/#sources>
- Rolling-tag pattern in `standard-actions`:
  `actions/publish/tag-and-release/action.yml`
