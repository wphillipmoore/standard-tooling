# Pushback Review: host-level-tool

**Date:** 2026-04-24
**Spec:** `docs/specs/host-level-tool.md` (replacement for the rejected
`docs/specs/git-url-dev-dependency.md`)
**Commit at review time:** 1af4f36
**Branch:** `feature/286-host-level-tool` (worktree:
`.worktrees/issue-286-host-level-tool/`)
**Related issue:** #286
**Outcome:** **Spec accepted after nine resolutions applied in-place.**

## TL;DR

Nine issues surfaced across feasibility, contradictions, ambiguity,
and omissions. All nine were resolved by direct edits to the spec.
One was dismissed as not applicable (rollback plan — fleet-of-one
fails forward). The remaining eight produced targeted rewrites,
two of them material: the dev-tree override mechanism changed
(`.venv-host` restored after the initial draft tried to retire it),
and the canonical host install flipped from `pip install` to
`uv tool install` (cross-platform compatibility, PEP 668 avoidance).

The spec is ready for implementation.

## Source Control Conflicts

**None — no conflicts with recent changes.** The spec's concrete
references all match current repo state as of commit 1af4f36:

- Rolling minor tag `v1.2` exists on the remote (latest patch
  `v1.2.2`); `v1.3` does not (pyproject reads `1.3.0` but no release
  cut).
- `standard-actions` `tag-and-release` force-updates the rolling
  minor tag on every patch release.
- Dev container images pre-bake via `git clone -b develop && uv pip
  install --system` in
  `standard-tooling-docker/docker/common/standard-tooling-uv.dockerfile`.
- `src/standard_tooling/bin/pre_commit_hook.py` contains the five
  branch/context checks the spec relocates.
- `src/standard_tooling/bin/commit.py` does no validation today
  (only message formatting).
- `standard-tooling-plugin/hooks/scripts/validate-on-edit.sh`
  error text still points at the sibling-checkout bootstrap guide.
- `scripts/bin/` no longer exists (removed in commit 32654cb).

## Issues Reviewed

### [1] Dev-tree override conflicts with this repo's dual-venv pattern

- **Category:** contradictions
- **Severity:** serious
- **Issue:** The draft's dev-tree override ran `uv sync --group dev`
  against `.venv/` on the host. But this repo's CLAUDE.md and
  bootstrap model define `.venv/` as the dev container's venv —
  shebangs point at `/workspace/.venv/...` and don't resolve on the
  host. Host-side `uv sync` would overwrite the container venv and
  vice versa. The spec asserted `.venv-host` "was always a
  workaround," but the shebang problem is structural.
- **Resolution:** Option A — `.venv-host` restored specifically and
  only as the dev-tree-override venv for this repo (and any sibling
  checkout testing unreleased `standard-tooling`). The spec now
  includes a "Why `.venv-host`, not `.venv`" subsection explaining
  the shebang reasoning. Migration text adjusted so only
  `standard-tooling` itself retains `.venv-host`; consumers remove
  it.

### [2] `pip install` into base Python env may require sudo / --user on Linux

- **Category:** feasibility
- **Severity:** moderate
- **Issue:** The draft's canonical install was `pip install` into
  the base Python env. Works on macOS Framework Python (user-owned),
  but on Linux with system Python it needs `sudo`, `--user`, or
  `--break-system-packages` (PEP 668). Also fails the "same env that
  hosts uv" framing when `uv` is installed via the standalone
  installer (no Python env to install into).
- **Resolution:** Option A — canonical install flipped to
  `uv tool install`. `pip install` demoted to "documented
  alternative." Comparison table rewritten to show platform
  behavior, including PEP 668. The primary-developer machine's
  existing `pip`-based install remains valid and does not need
  migration.

### [3] `git commit --amend` / `rebase` blocked by the env-var gate

- **Category:** feasibility
- **Severity:** moderate
- **Issue:** The draft's five-line gate rejected any `git commit`
  without `ST_COMMIT_CONTEXT=1`. But several legitimate workflows
  (`--amend`, `rebase -i` with reword/edit/squash, `cherry-pick`,
  `revert`, merge-conflict resolution) invoke `git commit` without
  going through `st-commit`. The original `pre_commit_hook.py`
  didn't have this problem because it checked branch state, not
  invocation source.
- **Resolution:** Option A — gate expanded to admit
  `GIT_REFLOG_ACTION` values (`amend`, `cherry-pick`, `revert`,
  `rebase*`, `merge*`) set by git itself during these derived-commit
  workflows. The gate grew from five lines to ten. Raw
  `git commit -m "..."` (which runs with `GIT_REFLOG_ACTION=commit`)
  remains blocked.

### [4] CI install path for non-Python consumers unspecified

- **Category:** omissions
- **Severity:** moderate
- **Issue:** The draft covered three deployment targets (host,
  Python project `.venv`, dev container image) but didn't address
  CI runners in consumer repos. The `standards-compliance`
  composite action in `standard-actions` currently clones
  `standard-tooling` and adds `scripts/bin/` to PATH — but
  `scripts/bin/` no longer exists.
- **Resolution:** CI collapses into the two existing targets
  (Python: `uv sync --group dev`; non-Python: dev container image
  pre-bake). No new install mechanism needed. The spec now requires
  `standards-compliance` (and any other `standard-actions`
  composite bootstrapping `standard-tooling` onto runners) to stop
  cloning the repo and instead rely on one of the two existing
  paths. Added a "CI install path" section and a new acceptance
  criterion.

### [5] `standard-tooling` listed as Python consumer that MUST declare itself

- **Category:** ambiguity
- **Severity:** minor
- **Issue:** The scope section listed `standard-tooling` itself
  under "Python consumers (MUST declare dev dep)" — a circular
  reference; the repo can't declare itself as a git-URL dev dep.
  It's self-hosted via `uv sync --group dev` (editable install of
  the repo itself into `.venv/` inside the container).
- **Resolution:** Option A — `standard-tooling` pulled out of the
  "Python consumers" list and given a distinct paragraph explaining
  the self-hosted case and why no declaration is needed.

### [6] Rollback plan not documented

- **Category:** omissions
- **Severity:** minor
- **Issue:** The draft specified coordinated changes across three
  repos (`standard-tooling`, `standard-tooling-docker`,
  `standard-actions`) plus a consumer sweep. No documented plan
  for "we merged this and something breaks, now what?"
- **Resolution:** **Dismissed.** Fleet-of-one; the producer and
  consumer are the same person. Standard practice is fail-forward.
  The individual-developer-impact scale makes big-bang migration
  acceptable, and a formal rollback plan would be overhead for a
  single-contributor project.

### [7] CLAUDE.md stale hook references

- **Category:** omissions
- **Severity:** minor
- **Issue:** The draft's acceptance criterion for CLAUDE.md updates
  named only "Consumption Model and Host bootstrap sections," but
  the file has hook references scattered in other sections
  (worktree convention block, Git Hooks subsection). Parallel stale
  references exist in `docs/git-hooks-and-validation.md`,
  `docs/site/docs/guides/git-workflow.md`, and
  `docs/site/docs/guides/consuming-repo-setup.md`.
- **Resolution:** Option A — acceptance criterion broadened to
  cover all stale `scripts/lib/git-hooks`, `.venv-host` (as a
  consumer install mechanism), and sibling-checkout references
  across CLAUDE.md and all of `docs/`. Verification grep embedded
  in the AC itself.

### [8] "Minimal" runtime deps description is inaccurate

- **Category:** ambiguity
- **Severity:** minor (wording)
- **Issue:** An earlier draft said `standard-tooling`'s runtime deps
  are "minimal"; actually `pyproject.toml` reads `dependencies = []`
  (zero deps — stdlib only).
- **Resolution:** Resolved incidentally during issue [2] — the
  `pip install` vs `uv tool install` comparison was rewritten to
  remove the "minimal deps" phrasing entirely.

### [9] Major-version bump behavior not explicit

- **Category:** ambiguity
- **Severity:** minor
- **Issue:** The spec extensively discussed the rolling **minor**
  tag `v1.2` but didn't address behavior at a **major** bump
  (`v1.x` → `v2.0`). The rolling tag is `v{major.minor}`, not
  `v{major}`, so major bumps are opt-in at every deployment target
  — correct behavior but undocumented.
- **Resolution:** Option A — added a "Major-version bumps"
  subsection under Tradeoffs explaining the intended behavior: no
  automatic propagation across major boundaries; explicit edits at
  each target to move.

## Unresolved Issues

None. All nine were addressed.

## Summary

- **Issues found:** 9
- **Issues resolved:** 8 (1 additionally dismissed as not applicable)
- **Unresolved:** 0
- **Spec status:** **Ready for implementation.** The spec can now be
  committed and #286 closed once the code work in the migration
  section lands.
