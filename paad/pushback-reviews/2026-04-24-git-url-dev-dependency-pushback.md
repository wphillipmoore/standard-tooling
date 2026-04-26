# Pushback Review: git-url-dev-dependency

**Date:** 2026-04-24
**Spec:** `docs/specs/git-url-dev-dependency.md` (landed on `develop` via PR #285)
**Commit at review time:** 56d5694
**Related issue:** #284 (fleet rollout tracking)
**Outcome:** **Spec rejected.** The git-URL dev-dependency approach is
Python-specific and cannot serve a heterogeneous fleet. Replacement direction
agreed: treat `standard-tooling` as a host-level developer tool.

## TL;DR

The spec proposed that every managed consumer repository declare
`standard-tooling` as a git-URL dev dependency in its `pyproject.toml` via
`[tool.uv.sources]`, pinned to a rolling minor tag. That framing treats the
problem as Python dependency management.

The fleet is not Python-shaped. Of the 5 non-deferred in-scope repos, only
`ai-research-methodology` (the pilot) is a `uv`-managed Python project. The
deferred `mq-rest-admin-*` family spans Python, Ruby, Go, Rust, and Java —
most also lack `pyproject.toml`. The pattern cannot reach the majority of
the fleet, including the repo (`standard-tooling-plugin`) whose failure
motivated the rollout.

The decision: **`standard-tooling` is a host-level developer tool**,
installed once into the developer's base Python environment (the same env
that hosts `uv`), upgraded via a documented one-liner as part of the
release workflow. No per-repo dependency wiring. PATH-based dev-tree
overrides remain available for testing unreleased versions.

## Source Control Conflicts

**One conflict, moderate severity.** The canonical example pins
`tag = "v1.3"`, but `v1.3` does not yet exist on the remote — the latest
published tag is `v1.2.2` and the rolling minor tag is `v1.2`.
(`pyproject.toml` sits at `version = "1.3.0"` but no release has been cut.)

User initially chose to rewrite the canonical example to use `v1.2`; that
resolution was superseded when the entire approach was abandoned.

## Issues Reviewed

### [1] Sequencing — spec points at an unreleased rolling-minor tag
- **Category:** feasibility
- **Severity:** moderate
- **Issue:** The canonical pin `tag = "v1.3"` cannot resolve today. Any
  consumer that follows the spec verbatim fails `uv lock` with
  tag-not-found.
- **Resolution:** Initially selected option B (rewrite example to `v1.2`
  with a note to bump on next minor release). Superseded by abandonment
  of the spec.

### [2] Pattern is Python-specific; fleet is heterogeneous
- **Category:** feasibility / scope imbalance
- **Severity:** serious (fatal to the spec)
- **Issue:** `[tool.uv.sources]` requires each consumer to be a
  `uv`-managed Python project with a `pyproject.toml`. Of the 5
  non-deferred in-scope repos:
  - `ai-research-methodology` — Python ✓
  - `standard-tooling-plugin` — Claude Code plugin (MD + JSON), **no
    `pyproject.toml`**
  - `standard-tooling-docker` — Dockerfiles + bash, **no `pyproject.toml`**
  - `the-infrastructure-mindset` — articles/docs, **no `pyproject.toml`**
  - `standards-and-conventions` — markdown standards, **no
    `pyproject.toml`**

  Adding a `pyproject.toml` to a docs or plugin repo solely to pin one
  dev dep is fighting the tools. The deferred `mq-rest-admin-*` family
  compounds this: services span Python/Ruby/Go/Rust/Java — also mostly
  non-Python.

  Issue #284 explicitly names `plugin#69` ("validator hooks dispatching
  via `st-docker-run`") as motivation, and cites the rollout as
  "[ensuring] `st-docker-run` is always in the consuming repo's venv."
  `standard-tooling-plugin` has no venv, so the spec does not solve the
  bug it was created to solve.
- **Resolution:** Spec abandoned. New direction (see below) moves tool
  availability from each consumer's dependency graph to the developer's
  host machine, making the fleet's language heterogeneity irrelevant.

## Unresolved Issues

Queued in severity order but not discussed, because the spec was
abandoned before they came up. Listed so the next attempt doesn't
rediscover them from scratch.

### [3] Plugin#69 is cited as driver but isn't solved by the spec
- **Category:** contradictions
- **Severity:** serious (subset of [2] but called out separately
  because it's the concrete bug that motivated the umbrella issue)
- **Issue:** `standard-tooling-plugin` is the primary driver for this
  rollout per #284, and is the clearest case the spec cannot address.

### [4] Contradiction — when do patches actually reach consumers?
- **Category:** contradictions
- **Severity:** moderate
- **Issue:** Line 54 states "new patches reach consumers on next sync";
  lines 172-175 correctly note that `uv sync` without `--refresh` uses
  the cached SHA from `uv.lock`. To pick up a patch, each consumer must
  run `uv lock --upgrade-package standard-tooling` and commit the
  lockfile — i.e., a dep-bump PR per consumer per patch. This
  undermines the rolling-tag approach's core argument against
  fixed-tag pinning.

### [5] Omission — git hooks and bash validators aren't installed by pip
- **Category:** omissions
- **Severity:** moderate
- **Issue:** The sibling-checkout convention serves two purposes:
  (a) Python `st-*` tools via `.venv-host/bin`, and (b)
  `core.hooksPath ../standard-tooling/scripts/lib/git-hooks` plus
  `scripts/bin/` bash validators. A pip/uv install places only the
  Python entry points into `.venv/bin/`; `scripts/lib/git-hooks/` and
  `scripts/bin/` live outside the wheel and do not ship. Consumers
  would still need a sibling checkout for those, defeating one of the
  rollout's primary goals.
- **Note:** A host-level install resolves this incidentally — the
  cloned source tree includes both directories. The follow-up spec
  should make this explicit and pick a canonical mechanism for
  enabling the hooks path.

### [6] Minor nits (not raised with the user)
- Issue #284 lists `infrastructure-mindset`; the on-disk repo is
  `the-infrastructure-mindset`.
- Issue #284's `mq-rest-admin-*` enumeration omits
  `mq-rest-admin-rust` (which exists in the fleet).

## New direction (for the follow-up spec)

Captured verbatim from the user's reframing so the replacement spec
can be drafted directly from this record.

1. **`standard-tooling` is a host-level tool**, on the same tier as
   `git`, `gh`, `uv`, and shell itself. It lives on `PATH` because the
   developer's machine has it, not because each repo declares it.
2. **Installation target:** the base Python environment on the
   developer's host — the same env that hosts `uv`. Mechanism: `pip
   install` (or `uv tool install`) from the GitHub git URL.
   `standard-tooling` is not and will not be on PyPI.
3. **Upgrade policy:** **manual, documented.** When a new release
   ships, developers run a documented one-liner to refresh their host
   install. Shell-startup auto-detection/auto-update was considered
   and **explicitly rejected** as a bad idea.
4. **Dev-tree override:** when testing an unreleased version, developers
   prepend the local checkout's venv to `PATH` ad-hoc. No special
   framework needed — `PATH` ordering wins.
5. **Per-project declaration is optional and discouraged.** Python
   consumers MAY still declare `standard-tooling` as a dev dep if
   there's a specific need; by default, the host install covers them.
6. **Non-Python consumers become first-class again.** Plugin, docker,
   docs, and all `mq-rest-admin-*` language variants get the tools the
   same way Python consumers do — via the host — with no per-repo
   shim, pyproject scaffold, or language-specific bootstrap.

### Open questions for the follow-up spec

- **`pip install` vs `uv tool install`.** `uv tool install` gives an
  isolated venv under `~/.local/share/uv/tools/` with console scripts
  symlinked to `~/.local/bin/`; `pip install` puts scripts wherever
  `pip` is called from. The user's stated model ("the same python bin
  that has `uv` will have `standard-tooling`") leans toward `pip install`
  into the base env, but `uv tool install` is cleaner. Not decided.
- **Exact release-time one-liner.** Likely
  `pip install --upgrade 'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.2'`
  using the rolling-minor tag so each run picks up the current patch.
  Depends on the rolling-tag behavior of `standard-actions`
  `tag-and-release` — verify before codifying.
- **Git hooks.** Consumers currently set
  `core.hooksPath ../standard-tooling/scripts/lib/git-hooks`. With a
  host install there is no sibling checkout. Options:
  (a) point `core.hooksPath` at the host-clone location exposed by
  `pip`/`uv tool install`; (b) route everything through a Python entry
  point (e.g., the existing `st-pre-commit-hook`); (c) each consumer
  vendors a thin shim that shells out to `st-pre-commit-hook`.
- **Enforcement.** The user acknowledged that "agent forgets to do the
  bootstrap" is the core failure mode, and that docs alone don't solve
  it. With a host-level install, the one-time bootstrap is out of
  per-session view entirely — but the *first* agent running on a fresh
  host still needs to know to run the install. Worth thinking about a
  fail-loud check somewhere (e.g., `st-docker-run` trip-wire in each
  consumer's task runner) even under the host-install model.

## Fate of the existing artifact

`docs/specs/git-url-dev-dependency.md` has already landed on `develop`
via PR #285. With the spec rejected, that file is stale guidance. It
needs one of:

- a replacement PR that deletes it (if the follow-up fully supersedes),
- a replacement PR that rewrites it in place as the host-level-tool
  spec, or
- a short "superseded by" header added at the top, pointing at the
  follow-up spec — left in place as a historical artifact.

Issue #284 is also invalidated in its current form (the rollout
checklist doesn't apply) and will need closure or a substantial rewrite
once the follow-up spec lands.

## Summary

- **Issues found:** 6
- **Issues resolved:** 0 (spec abandoned before any resolution took
  effect)
- **Spec status:** **rejected**. Replacement direction agreed; follow-up
  spec to be written in a separate session.
