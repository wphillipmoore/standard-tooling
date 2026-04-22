# Alignment Review: worktree-convention

**Date:** 2026-04-22
**Commit:** `93234cc6c98436ea9c6dcfa862e89386a6fcd320`
**Issue:** [#258](https://github.com/wphillipmoore/standard-tooling/issues/258)
**Reviewer:** Claude (paad:alignment skill, Opus 4.7)
**Disposition:** Plan updated in place with the one resolution.

## Documents Reviewed

- **Intent:** `docs/specs/worktree-convention.md` (post-pushback
  revision)
- **Action:** `docs/plans/worktree-convention-plan.md` (initial draft)
- **Design:** none — the spec's **Rollout plan** section is the
  design; no intermediate design layer.

## Source Control Conflicts

None. Git log was reviewed during the preceding `paad:pushback`
pass. No new commits have landed since, so the pushback reality
check still holds.

## Alignment Summary (overview)

Coverage and scope are both tight. Pushback did most of the cleanup
work before the plan was drafted, so the plan was written against an
already-scrubbed spec.

- **Requirements coverage:** Every substantive spec requirement
  maps to at least one plan task. Deferred items (enforcement
  tooling, adjacent work) are explicitly tracked in Plan Task 1.6
  rather than silently dropped.
- **Scope compliance:** Every plan task traces back to a spec
  requirement or an operationally-necessary wrapper (PR workflow,
  issue bookkeeping). No scope creep, no gold-plating.
- **Design alignment:** N/A (no intermediate design doc).

## Issues Reviewed

### [1] Plan Task 2.3 verification didn't assert memory sharing — the spec's load-bearing claim

- **Category:** missing coverage
- **Severity:** important
- **Documents:** spec **Memory-path implications** section ↔ plan
  **Task 2.3**
- **Issue:** The spec describes memory-path sharing as *"the
  load-bearing constraint for the whole design."* The pilot (Task
  2.3) is the spec's designated live validation of that claim.
  Original verification wording only checked *"without memory-silo
  surprises"* — passive, no assertable signal. Failure-mode gap:
  if one pilot session was started inside `.worktrees/<name>/`
  instead of at the project root, git-level isolation would still
  prevent collisions (both agents commit to their own branches
  fine) while memory sharing silently failed (different slug →
  different memory silo). The pilot could be declared successful
  while missing the load-bearing validation.
- **Resolution:** Plan Task 2.3 updated in-place to:
  - Require `pwd` confirmation before launching each session (must
    equal the pilot repo root).
  - Split verification into two explicit checks:
    - **Collision prevention (git-level)** — the original check.
    - **Memory-path sharing (load-bearing claim)** — assert that
      `ls -d ~/.claude/projects/*dev-github-<pilot-repo-name>`
      resolves to exactly one matching directory. Zero matches
      means neither session registered; two matches means a
      session was started from the wrong CWD and rule 1 was
      violated.
  - Added an explicit statement that the pilot is **not**
    successful if the memory-path check fails, even if collision
    prevention passed. This prevents a "false green" pilot outcome.

## Minor Observations (batched, not individually discussed)

These are nitpick-tier and were explicitly skipped during the
review. Recorded here for completeness in case they become relevant
during implementation:

- **Cleanup guidance is spec-only** — Plan 1.2 doesn't surface
  cleanup commands in CLAUDE.md. Users at branch-land have to
  click through to the spec. Would add 3–5 lines to CLAUDE.md.
- **Stacked-worktree guidance is spec-only** — Intentional (it's
  the exception case per the spec). Not flagged as a gap.
- **Plan 1.3's dry-run verifies mechanics, not rules** — Rules are
  validated only in Phase 2 (pilot). This is by design: Phase 1 is
  "convention present" and Phase 2 is "convention validated."
- **Plan 1.2's 40–80 line CLAUDE.md budget isn't in the spec** —
  Reasonable implementation choice; doesn't contradict the spec.

## Unresolved Issues

None.

## TDD Task Rewrite

**Skipped.** Per the `paad:alignment` skill guidance: *"Skip this
step if tasks don't involve code implementation (e.g., infrastructure
provisioning, documentation, design work, data migrations, manual
processes)."* Every task in the plan is one of:

- `.gitignore` / CLAUDE.md / spec edits (documentation)
- Manual dry-runs, parallel-agent pilot runs, PR workflow (manual
  processes)
- Issue bookkeeping, retrospective notes (manual processes)

No code implementation. TDD rewrite would force a red/green/refactor
structure onto tasks where there is no unit to test.

## Alignment Summary (final)

- **Requirements:** ~17 substantive items in the spec; all have
  plan coverage or are explicitly deferred to follow-up.
- **Tasks:** 17 plan tasks across 5 phases; every one traces to a
  spec requirement or an operational wrapper. No orphans.
- **Design items:** N/A.
- **Issues found:** 1 important coverage gap (resolved) + 4 minor
  observations (acknowledged, skipped).
- **Status:** Aligned. Plan is ready to execute starting with
  Phase 1 (this repo: `.gitignore` + CLAUDE.md update, follow-up
  issues).

## Related Artifacts

- Spec: `docs/specs/worktree-convention.md`
- Plan: `docs/plans/worktree-convention-plan.md`
- Pushback review: `paad/pushback-reviews/2026-04-22-worktree-convention-pushback.md`
