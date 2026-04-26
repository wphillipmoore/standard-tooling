# Alignment Review: host-level-tool

**Date:** 2026-04-25
**Commit at review time:** 1af4f36
**Branch:** `feature/286-host-level-tool` (worktree:
`.worktrees/issue-286-host-level-tool/`)

## Documents Reviewed

- **Intent:** `docs/specs/host-level-tool.md`
- **Action:** `docs/plans/host-level-tool-plan.md`
- **Design:** none

## Source Control Conflicts

**None — no conflicts with recent changes.** Repo state at 1af4f36
matches all assumptions in both documents (rolling tag mechanics,
image pre-bake script, current `commit.py` and `pre_commit_hook.py`
contents, `scripts/bin/` removal, `validate-on-edit.sh` error text).

## Issues Reviewed

### [1] Plan references incorrect test file paths

- **Category:** missing coverage (factual error)
- **Severity:** Important
- **Documents:** Plan Phase 1 Tasks 1.1 and 1.4
- **Issue:** Plan referenced `tests/bin/test_commit.py` and
  `tests/bin/test_pre_commit_hook.py`. Actual paths are
  `tests/standard_tooling/test_commit.py` and
  `tests/standard_tooling/test_pre_commit_hook.py`. The
  `tests/bin/` directory does not exist in the repo.
- **Resolution:** Both path references corrected in-place in the
  plan.

### [2] Phase 2 Task 2.1 has confused version-bump guidance

- **Category:** ambiguity (in plan)
- **Severity:** Minor
- **Documents:** Plan Phase 2 Task 2.1
- **Issue:** Original text described "bump from 1.3.0 to 1.3.0
  (already there)" with a confusing fallback to a `1.2.3` patch
  scenario. Also did not address the strict-semver question raised
  by removing the `st-pre-commit-hook` entry point (technically a
  breaking change worthy of `v2.0.0`).
- **Resolution:** Option A — clean `v1.3.0` bump documented;
  release notes call out the entry-point removal as a clean break;
  the strict-semver-vs-fleet-of-one tradeoff is named explicitly.
  Convoluted fallback text removed.

### [3] Phase 7 doesn't explicitly call out the four-step getting-started flow

- **Category:** missing coverage
- **Severity:** Minor
- **Documents:** Spec acceptance criterion ↔ Plan Phase 7
- **Issue:** Spec acceptance criterion calls out "Getting-started
  docs updated to the four-step flow in [First-time developer
  setup]." Plan's Phase 7 is described as a generic grep-and-rewrite
  sweep, which would catch removal of stale references but does not
  ensure the new four-step narrative actually appears in the canonical
  getting-started doc.
- **Resolution:** Option A — added Task 7.5 "Rewrite the canonical
  getting-started narrative" with a verification that a fresh reader
  on a clean machine can follow the doc top-to-bottom and end with
  working `st-docker-run --help`. Phase 7 exit criteria expanded
  to require the new narrative.

### [4] Phase 1 lacks dev-tree override verification

- **Category:** missing coverage (verification gap)
- **Severity:** Minor
- **Documents:** Spec Principle 4 / Dev-tree override section ↔
  Plan Phase 1
- **Issue:** The `.venv-host` dev-tree override survived as a
  spec requirement after pushback issue [1]. Plan's Phase 1 changes
  code paths but never verifies the override workflow still works
  after those changes — silent breakage risk.
- **Resolution:** Option A — Task 1.6 ("Validate the full pipeline
  locally") gained a sub-check that exercises
  `UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev` and the
  PATH-prepended override, with explicit verification that
  `which st-docker-run` resolves to `.venv-host/bin/...`.

### [5] Phase 6 verification doesn't match spec verification language

- **Category:** missing coverage
- **Severity:** Minor
- **Documents:** Spec "Migration / Non-Python consumers" ↔ Plan
  Phase 6 Tasks 6.1-6.4
- **Issue:** Spec verification step requires confirming the image's
  pre-baked `st-*` is what runs inside the container — the
  operationally meaningful check that catches stale-image silent
  failures (the `standard-tooling-docker#51` failure mode). Plan
  Tasks 6.1-6.4 omitted this check, only verifying `core.hooksPath`
  setup and plugin hook firing.
- **Resolution:** Option A — Task 6.1 verification expanded with
  an "Image pre-bake provenance check" subsection (`st-docker-run
  -- which st-validate-local` + `pip show standard-tooling`).
  Tasks 6.2-6.4 reference the same check by phrase ("Same as 6.1,
  including the image-pre-bake provenance check").

## Unresolved Issues

None. All five issues addressed; document edits applied in-place
to `docs/plans/host-level-tool-plan.md`.

## TDD Rewrite

After alignment was confirmed, Phase 1 Tasks 1.1, 1.2, and 1.3
(the code-implementation tasks) were rewritten in red/green/refactor
format per the alignment skill's TDD step. Other phases
(infrastructure provisioning, docs sweep, migration, process) were
not TDD-amenable and remain in original task format.

The TDD rewrites pin behavior contracts that the spec emphasizes:

- **Task 1.1 RED:** ten failing tests in
  `tests/standard_tooling/test_commit.py` covering one rejection
  - one happy path for each of the five branch/context checks.
- **Task 1.2 RED:** failing test asserting
  `os.environ["ST_COMMIT_CONTEXT"] == "1"` is captured at the
  moment `git.run("commit", ...)` is invoked (the spec's required
  unit test).
- **Task 1.3 RED:** failing test invoking the gate via
  `subprocess.run(["bash", ".githooks/pre-commit"], env=...)`,
  exercising admit-by-env, admit-by-`GIT_REFLOG_ACTION`, and reject
  branches.

REFACTOR sections in each task name specific candidates for
consolidation (constants extraction, helper functions) and also
specific candidates for *not* refactoring (e.g., promoting
`"ST_COMMIT_CONTEXT"` to a constant — premature given a single
Python reference).

## Alignment Summary

- **Spec acceptance criteria:** 9 total, 9 addressed in the plan
- **Spec migration steps (across 4 tracks):** ~16 total, all
  addressed
- **Spec six principles:** 6 total, 6 mapped to plan phases
- **Plan tasks:** 30+ total, all trace to spec requirements;
  none orphaned
- **Plan tasks rewritten in TDD format:** 3 (Tasks 1.1, 1.2, 1.3)
- **Status:** **Aligned.** Plan is ready for implementation pending
  commit/PR/merge of the spec + plan + pushback report + alignment
  report bundle.
