# Implementation Plan: Git Worktree Convention

**Status:** Draft — awaiting `paad:alignment` against the spec
**Spec:** [`docs/specs/worktree-convention.md`](../../specs/worktree-convention.md)
**Issue:** [#258](https://github.com/wphillipmoore/standard-tooling/issues/258)
**Last updated:** 2026-04-22

## Scope

This plan covers implementation of the worktree convention as defined
in the spec. Rollout is sequenced in five phases that map directly to
the spec's **Rollout plan** section:

1. Land the convention in `standard-tooling` (this repo).
2. Pilot the convention in one active-parallel repo.
3. Cascade to the remaining consuming repos.
4. Canonicalize in `standards-and-conventions`.
5. Retrospective and feedback-memory capture.

Each phase has observable completion criteria and a defined blocker
or handoff to the next phase.

## Out of scope for this plan

Tracked separately, per the spec's **Enforcement and follow-up work**
and **Adjacent work surfaced during pushback** sections. Each gets
its own issue (opened in Phase 1, Task 1.6):

- Git hook that refuses commits from the project root (enforcement
  backstop for rules 1–3).
- `st-finalize-repo` extension: worktree removal for the finalized
  branch (implements the Cleanup section's canonical flow).
- `st-worktree-prompt` helper: emits the canonical prompt template
  given `<issue-number>` and `<slug>`.
- `st-worktree-prune` (optional, needs-driven, for abandoned
  branches).
- MEMORY.md ban removal in this repo's CLAUDE.md (and fleet-wide
  where applicable). **Blocks Phase 5 feedback-memory capture.**
- Deprecation of the "include this doc and remember it" pattern
  fleet-wide.

## Phase 1: Land the convention in `standard-tooling`

**Goal:** The canonical convention text lives in this repo's
CLAUDE.md and `.worktrees/` is gitignored, so that when someone
starts using worktrees here, the convention governs their behavior.

### Task 1.1: Add `.worktrees/` to `.gitignore`

- **Action:** Append `.worktrees/` to `/.gitignore`.
- **Verification:** `git check-ignore -v .worktrees/any-path` returns
  exit 0 and points at the new rule.

### Task 1.2: Add a Parallel AI agent development section to `CLAUDE.md`

- **Action:** Add a new section (after existing "Auto-memory policy"
  or similar top-of-file location) that covers:
  - The structure (`~/dev/github/standard-tooling/.worktrees/...`)
  - The five rules (verbatim from the spec)
  - A pointer to the canonical spec
    (`docs/specs/worktree-convention.md`)
  - The Agent prompt contract (canonical template, copy-pasteable)
- **Length guideline:** Short enough to be read every session —
  roughly 40–80 lines. Push the full design (Problem statement, Trust
  model, Memory-path implications, Failure modes) to the linked
  spec, not CLAUDE.md.
- **Verification:**
  - `grep -q "Parallel AI agent development" CLAUDE.md`
  - `grep -q "Your worktree is:" CLAUDE.md` (prompt template marker)
  - Spec link resolves (`docs/specs/worktree-convention.md` exists)

### Task 1.3: Verify the rules actually work in this repo

- **Action:** Dry-run the onboarding procedure against a throwaway
  issue number:
  - `git worktree add .worktrees/test-worktree-convention -b
    test/worktree-convention origin/develop`
  - Confirm `.worktrees/` stays gitignored (main tree status clean).
  - Confirm `cd .worktrees/test-worktree-convention && git status`
    reports the feature branch.
  - Confirm `st-docker-run` from inside the worktree mounts that
    directory (not the main tree).
  - Clean up: `git worktree remove .worktrees/test-worktree-convention
    && git branch -D test/worktree-convention`.
- **Verification:** Shell session transcript (or a note in the PR
  description) confirming each step.

### Task 1.4: Open the PR, get it merged, `st-finalize-repo`

- **Action:** Follow the standard PR workflow. PR body references
  #258 and summarizes the convention in one paragraph.
- **Verification:** PR merged to `develop`; `st-finalize-repo` run;
  issue #258 remains open (Phase 5 wraps it up).

### Task 1.5: Update issue #258 acceptance criteria

- **Action:** Tick off "This repo: `.gitignore` + CLAUDE.md updated"
  in #258's acceptance criteria. Post a short comment linking to the
  PR.
- **Verification:** #258 shows the item checked.

### Task 1.6: Open follow-up issues for the deferred items

- **Action:** Open one issue per deferred item from the
  "Out of scope for this plan" list above. Each issue references
  #258 and the spec's **Enforcement and follow-up work** section.
  At minimum:
  - Git hook: refuse commits from project root / outside
    `.worktrees/*`.
  - `st-finalize-repo`: worktree-aware cleanup.
  - MEMORY.md ban removal (this repo).
  - Include-pattern deprecation (cross-repo; may be filed in
    `standards-and-conventions` instead).
  - (Optional, defer if unsure) `st-worktree-prompt` helper.
- **Verification:** All issues created and linked from #258's
  "Related" section.

**Phase 1 exit criteria:** PR merged. `.gitignore` and CLAUDE.md
updated. Dry-run successful. Follow-up issues filed. No pilot work
starts before this phase lands.

## Phase 2: Pilot in an active-parallel repo

**Goal:** Use the convention end-to-end in a repo where parallel
agent work actually happens, surface gaps that only appear in live
use, and feed those gaps back into the spec before fleet cascade.

### Task 2.1: Choose the pilot repo

- **Action:** Pick whichever of `the-infrastructure-mindset` or
  `ai-research-methodology` has imminent parallel-agent work. Default
  to `the-infrastructure-mindset` if both are equally active, since
  the 2026-04-22 collision originated there and makes a natural
  before/after comparison.
- **Verification:** Decision recorded in #258 as a comment, with the
  next parallel-agent work item that will test the convention.

### Task 2.2: Apply the convention to the pilot repo

- **Action:** In the pilot repo:
  - Add `.worktrees/` to `.gitignore`.
  - Add the Parallel AI agent development section to its CLAUDE.md
    (same body as Phase 1 Task 1.2, with repo-specific paths).
- **Verification:** Pilot repo's CLAUDE.md and `.gitignore` updated
  via PR; merged.

### Task 2.3: Run two parallel agents using the convention

- **Action:** Start two Claude Code sessions at the pilot repo's
  root. Before launching each session, run `pwd` and confirm the
  output is the pilot repo's root path — **not** a worktree path.
  Then use the canonical prompt template to assign each session a
  worktree on a different feature branch. Let them work to
  completion (or at least through a first round of file edits +
  commits).
- **Verification:**
  - **Collision prevention (git-level):** Both agents complete their
    work without filesystem collisions and without committing to
    the wrong branch. Git log for each feature branch shows only
    that worktree's commits.
  - **Memory-path sharing (load-bearing claim):** After both
    sessions have started, assert that both resolve to the same
    Claude Code memory directory. Run:

    ```bash
    ls -d ~/.claude/projects/*dev-github-<pilot-repo-name> 2>/dev/null
    ```

    Exactly one directory should match — the shared slug derived
    from the pilot repo root. Zero matches means neither session
    registered; two matches means a session was started from the
    wrong CWD and memory silos diverged (rule 1 violation). The
    pilot is **not** successful if this check fails, even if
    collision prevention passed.

### Task 2.4: Capture pilot findings

- **Action:** Write a short findings note (as a comment on #258 or
  an appended section to the spec). Cover:
  - What worked as specified.
  - What needed clarification in the prompt template.
  - Any failure-mode entries that should be added / removed.
  - Any rules whose wording proved ambiguous in live use.
- **Verification:** Findings posted; spec PR opened for any
  amendments (or marked "no amendments needed").

**Phase 2 exit criteria:** Pilot completed, findings recorded. Spec
revised if needed. Cascade does not start until spec is stable post-
pilot.

## Phase 3: Fleet cascade

**Goal:** Every active consuming repo carries the convention so any
future parallel-agent work has the infrastructure in place.

### Task 3.1: Cascade to remaining active-parallel repo

- **Action:** Whichever of `the-infrastructure-mindset` /
  `ai-research-methodology` was not the pilot: apply `.gitignore` +
  CLAUDE.md changes. PR + merge.
- **Verification:** Repo's CLAUDE.md and `.gitignore` updated.

### Task 3.2: Cascade to the remaining fleet

- **Action:** In priority order, apply the same two-file change:
  1. `mq-rest-admin-python` (most active Python repo)
  2. Remainder of `mq-rest-admin-*`
  3. `standard-actions`
  4. `standard-tooling-docker`
  5. `standard-tooling-plugin`
  6. `mempalace`
- **Verification:** One PR per repo; all merged. A short checklist
  in #258 tracks the progress.

**Phase 3 exit criteria:** Every actively developed repo listed in
the spec carries the convention.

## Phase 4: Canonicalize in `standards-and-conventions`

**Goal:** New repos have a reference to point at; future fleet-wide
conversations have a single canonical doc to cite.

### Task 4.1: Author the generalized write-up

- **Action:** Port this spec to `standards-and-conventions`,
  removing repo-specific paths and the rollout/retrospective sections
  (keep the convention, rules, prompt contract, trust model, memory-
  path implications). Reference the standard-tooling spec as the
  implementation anchor.
- **Verification:** `standards-and-conventions` PR merged containing
  the generalized doc.

### Task 4.2: Update the fleet's CLAUDE.md entries to reference the canonical doc

- **Action:** In each repo that received the convention in Phases
  1–3, update the CLAUDE.md section to reference the canonical
  doc in `standards-and-conventions` (in addition to — not instead
  of — the repo-local pointer).
- **Verification:** Each repo's CLAUDE.md cites the canonical doc.

**Phase 4 exit criteria:** Canonical doc published. Fleet CLAUDE.md
entries cross-reference it. No automatic inheritance is implied or
required.

## Phase 5: Retrospective and feedback-memory capture

**Goal:** Close out the PAAD pilot, record what was learned, and
(once unblocked) add the agent-facing feedback memory.

### Task 5.1: Retrospective notes on ai-research-methodology #129

- **Action:** Add a comment or linked doc to
  `ai-research-methodology#129` covering what worked and what
  didn't in the PAAD spec → pushback → alignment → implementation
  cycle for this issue. This is the second PAAD pilot; the first was
  ai-research-methodology#135.
- **Verification:** Comment posted on #129 referencing this spec,
  this plan, and the pushback review.

### Task 5.2: Capture feedback memory (blocked until MEMORY.md ban lifted)

- **Action:** In each repo where the MEMORY.md ban has been lifted
  (see Phase 1 Task 1.6's follow-up issue), add a feedback memory:
  *"When told to work on issue N, your worktree is
  `.worktrees/issue-N-<slug>/`. Do git operations there; for file
  edits use the worktree's absolute path, for Bash file commands
  `cd` into the worktree first or use absolute paths."*
- **Blocker:** The MEMORY.md ban removal must land first (tracked as
  its own follow-up issue). This task waits.
- **Verification:** Each participating repo's memory index includes
  the entry.

### Task 5.3: Close #258

- **Action:** Verify every acceptance-criteria checkbox is ticked or
  explicitly deferred with a linked follow-up. Close the issue.
- **Verification:** #258 closed with a link to the completed work.

**Phase 5 exit criteria:** #258 closed. Retrospective landed.
Feedback-memory entries in place in every repo that permits them.

## Dependencies and blockers

| Depends on | Blocks | Notes |
|------------|--------|-------|
| Phase 1 complete | Phases 2–5 | Nothing cascades until this repo carries the convention |
| Phase 2 complete (pilot findings) | Phase 3 cascade | Cascade happens after pilot validates (or amends) the spec |
| Phase 3 + 4 cross-references | Phase 4 Task 4.2 | Canonical doc must exist before repos cite it |
| MEMORY.md ban removal issue | Phase 5 Task 5.2 | Feedback memory cannot be captured where the ban still applies |
| No hard dependency on enforcement-tooling follow-ups | — | Enforcement is a backstop, not a gate |

## Success criteria (aggregated)

Mapped to the spec's acceptance criteria:

- [x] Design spec authored (already complete per pushback review)
- [x] `paad:pushback` run on spec (complete; see
  `paad/pushback-reviews/2026-04-22-worktree-convention-pushback.md`)
- [ ] `paad:alignment` run between this plan and the spec
  (next paad step after this plan is drafted)
- [ ] Phase 1 complete (this repo)
- [ ] Phase 2 complete (pilot)
- [ ] Phase 3 complete (fleet cascade)
- [ ] Phase 4 complete (canonical doc)
- [ ] Phase 5 complete (retrospective + feedback memory)
- [ ] All follow-up issues from Phase 1 Task 1.6 tracked (not
  necessarily implemented; tracked is enough)
