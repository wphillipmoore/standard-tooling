# Pushback Review: worktree-convention.md

**Date:** 2026-04-22
**Spec:** `docs/specs/worktree-convention.md`
**Commit:** `93234cc6c98436ea9c6dcfa862e89386a6fcd320`
**Issue:** [#258](https://github.com/wphillipmoore/standard-tooling/issues/258)
**Reviewer:** Claude (paad:pushback skill, Opus 4.7)
**Disposition:** Spec updated in place with all resolutions.

## Source Control Conflicts

One conflict surfaced in Phase 1.

### Conflict [1]: "Agent-facing feedback memory" contradicted this repo's MEMORY.md ban

- **Spec assumption:** Cross-repo propagation item 4 proposed writing
  a "per-repo feedback memory" capturing the worktree assignment rule.
- **Actual state:** Commit `4561dcf` (#225, 2026-03-08) added an
  "Auto-memory policy" section to CLAUDE.md forbidding MEMORY.md /
  memory-directory writes in standard-tooling, deferring to
  version-controlled docs. Upstream fixes
  `standards-and-conventions#347`.
- **Resolution:** The MEMORY.md ban is an anachronism from the
  polyglot-convergence era (five per-language repos, trying to get
  consistent agent behavior across them via memory). The author has
  since found feedback memory to be high-value in active repositories
  (`the-infrastructure-mindset`). The ban will be removed in this
  repo as adjacent work. The spec's item 5 (renumbered during
  revision) stands.
- **Flagged as adjacent work** in the spec's
  "Adjacent work surfaced during pushback" section.

## Phase 1.5: Scope Shape

- **Cohesion:** Single coherent feature (a methodology convention +
  its rollout). Not flagged.
- **Size:** Wide but shallow — each repo's change is a `.gitignore`
  line plus a CLAUDE.md paragraph. Not flagged.

## Issues Reviewed

### [1] Agent prompt contract is underspecified

- **Category:** omission
- **Severity:** serious
- **Issue:** The whole convention rests on each parallel agent being
  told, via the session prompt, which worktree it owns. The original
  spec described this informally. Without a canonical contract, each
  launch gets worded differently and the load-bearing mechanism
  fails silently — agents without a worktree assignment default to
  the main tree and reproduce the original collision.
- **Resolution:** Added an **Agent prompt contract** section to the
  spec with a canonical, copy-paste prompt template. All fields
  (issue number, absolute worktree path, branch, behavior rules)
  are marked required. A future `st-worktree-prompt` helper is
  flagged as follow-up. Enforcement tooling (git hook / `st-*` /
  plugin) is tracked as a separate follow-up bucket under
  **Enforcement and follow-up work** — with the design principle
  that enforcement is a safety net, not the primary mechanism.

### [2] "Main worktree is read-only" rule was overreaching as stated

- **Category:** ambiguity / contradiction
- **Severity:** serious
- **Issue:** Original wording read *"read-only while parallel work is
  in flight."* Taken literally, this forbade any edit at the project
  root whenever any `.worktrees/*` existed — blocking unrelated
  CLAUDE.md fixes, docs tweaks, and dependency bumps. The actual
  failure mode was narrower: dirty state at the root + concurrent
  readers.
- **Resolution:** Author clarified that the repo has a standing
  policy of **no direct commits to develop** — all changes flow
  through feature branches via PR. Given that, the rule is not an
  overreach; it is the logical endpoint of the existing policy. The
  rule was reframed: *"The main worktree is read-only. All edits
  flow through a worktree on a feature branch. This is the logical
  endpoint of the standing 'no direct commits to develop' policy."*
  The same git hook that refuses direct pushes to develop is the
  natural place to refuse commits from outside `.worktrees/*`
  (tracked under Enforcement and follow-up work).

### [3] Cleanup procedure ignored the existing `st-finalize-repo`

- **Category:** omission
- **Severity:** moderate
- **Issue:** Original Cleanup section prescribed raw `git worktree
  remove` / `git branch -D`. This repo already ships
  `st-finalize-repo` for post-merge cleanup (branch deletion,
  remote pruning, and now container validation per #254). The
  spec's recipe overlapped with and diverged from that tool — two
  mental models, drift risk, worktree residue after
  `st-finalize-repo` ran.
- **Resolution:** Spec's Cleanup section now prescribes
  `st-finalize-repo` as the canonical flow, with raw git as an
  interim procedure until the tool is extended to be worktree-aware.
  The `st-finalize-repo` extension is tracked under Enforcement and
  follow-up work. A separate `st-worktree-prune` helper is **not**
  pre-built — deferred until the abandoned-branch case (branches
  that never merge) proves a felt need.

### [4] Rollout order put the canonical write-up first, but the convention isn't settled yet

- **Category:** scope imbalance / sequencing
- **Severity:** moderate
- **Issue:** Original rollout: standards-and-conventions → standard-tooling
  → active consuming repos. That enshrined the canonical doc before
  the convention had been used in anger, and put the two repos with
  active parallel-agent work (`the-infrastructure-mindset`,
  `ai-research-methodology`) third. Any pilot-driven refinement
  would propagate back up as amendments.
- **Resolution:** Reordered in the spec's **Rollout plan** section:
  (1) standard-tooling first (docs + gitignore; tooling extensions
  follow), (2) pilot in an active-parallel repo, (3) fleet cascade,
  (4) canonicalize in standards-and-conventions last. Canonical doc
  now reflects what the pilot validated rather than projecting a
  premature standard.

### [5] "Existing include/reference mechanism" claim was not accurate

- **Category:** factual accuracy
- **Severity:** moderate
- **Issue:** Spec wording implied that new repos would automatically
  "pick up" the convention via a standards-and-conventions
  inheritance mechanism. No such mechanism exists in practice; each
  repo's CLAUDE.md is hand-authored and updated manually.
- **Resolution:** Author confirmed the include mechanism is a
  **second anachronism**, from the same era as the MEMORY.md ban —
  an attempt to solve polyglot-convergence via "go read this and
  remember it" that caused context overload and did not work. The
  spec's wording was rewritten throughout: adoption is per-repo, the
  canonical doc is a human-readable reference, no inheritance is
  implied. Deprecation of the include pattern fleet-wide is flagged
  as adjacent work.

### [6] "Absolute paths for file edits" rule was redundant + confusing

- **Category:** ambiguity
- **Severity:** minor
- **Issue:** Original rule 2 said *"use absolute paths for file
  edits."* Read/Edit/Write already require absolute paths by tool
  contract, so the rule was a no-op for those cases. The actual
  distinction it was trying to make was about Bash commands that
  resolve paths against CWD.
- **Resolution:** Split into two explicit sub-rules under rule 2:
  (a) Read/Edit/Write must use the worktree's absolute path;
  (b) Bash commands that touch files must `cd` into the worktree
  first or use absolute paths. The distinction matches the actual
  decision the agent needs to make.

### [7] Stacked PRs / dependent worktrees unaddressed

- **Category:** omission
- **Severity:** minor
- **Issue:** Spec's onboarding example branched from
  `origin/develop`; the case where issue B depends on issue A's
  unmerged branch was silent.
- **Resolution:** Added one paragraph to Onboarding documenting the
  mechanism (substitute the parent branch in the worktree-add
  command), **explicitly framed as the exception** with a "prefer
  to defer dependent work or integrate it into the parent" note.
  Author emphasized: stacking is the special case, not the norm.

### [8] Worktree isolation is advisory only against intentional / buggy out-of-worktree writes

- **Category:** security / blast radius
- **Severity:** minor
- **Issue:** Git isolates branches per worktree, so *accidental
  version-control* collisions are prevented structurally. But the
  filesystem is not isolated — an agent can `Write` to a sibling
  worktree or the main tree. The 2026-04-22 incident was accidental;
  this design addresses it. It does not address "agent misreads its
  prompt and edits a sibling worktree."
- **Resolution:** Added a **Trust model** section to the spec that
  explicitly names what isolation does (git-level, accidental-path)
  and does not (filesystem sandbox) buy. The enforcement-tooling
  git hook (refuses commits from outside `.worktrees/*`) is the
  real backstop; uncommitted out-of-worktree edits remain a residual
  risk caught only by review. A true filesystem sandbox (devcontainer
  with selective mounts) is flagged as out of scope with reasoning.

### [9] Shared-cache concurrency under parallel tooling (demoted, not discussed in depth)

- **Category:** omission (failure modes)
- **Severity:** minor
- **Issue (considered):** Two worktrees running `uv sync` or
  `st-docker-test` in parallel could race on user-global caches
  (`~/.cache/uv`, etc.).
- **Disposition:** Demoted after analysis. `uv` locks its cache;
  dev-container `.venv` is per-invocation and worktree-local via
  the mount; pytest cache is in-tree per worktree. Not added to
  failure modes. Noted here for completeness.

## Unresolved Issues

None. All issues surfaced during the review were either resolved
through spec revision or explicitly deferred to a tracked follow-up
item with rationale.

## Adjacent Work Identified

The pushback surfaced two items that are not part of this spec's
implementation but are coupled:

- **Remove the MEMORY.md ban** in this repo's CLAUDE.md (and anywhere
  else it still lives in the fleet). Blocks cross-repo propagation
  step 5 (agent-facing feedback memory).
- **Deprecate the "include / reference and remember" pattern**
  fleet-wide. Replace with explicit per-repo CLAUDE.md entries — the
  model this spec already assumes.

Both are captured in the revised spec's
**Adjacent work surfaced during pushback** section.

## Follow-up Work Identified

The enforcement / tooling story is intentionally not in scope for
this spec, but the review identified concrete candidates to track
separately:

- Git hook that refuses commits from the project root (and/or from
  outside `.worktrees/*`) when rule 3 applies.
- `st-finalize-repo` extension: remove the worktree for the branch
  being finalized.
- `st-worktree-prompt` helper: emit the canonical prompt template
  given an issue number + slug.
- (Optional, needs-driven) `st-worktree-prune` for abandoned branches.
- (Optional, larger scope) Claude Code plugin that produces
  worktree + prompt automatically on work-item assignment.

Captured in the revised spec's **Enforcement and follow-up work**
section with the design principle: *the convention works without
these; they raise the floor on consistency, they do not gate
adoption.*

## Summary

- **Issues found:** 9 (8 discussed in depth; 1 demoted after analysis)
- **Source control conflicts found:** 1 (resolved — anachronism)
- **Issues resolved:** 9 of 9
- **Adjacent work items flagged:** 2 (MEMORY.md ban removal;
  deprecation of the include pattern)
- **Follow-up work items flagged:** 4–5
- **Spec status:** Ready for `paad:alignment` between the spec and
  an implementation plan, and for initial implementation of rollout
  step 1 (this repo's `.gitignore` + CLAUDE.md update).
