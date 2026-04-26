# Implementation Plan: `standard-tooling` as a host-level developer tool

**Status:** Draft — awaiting `paad:alignment` against the spec
**Spec:** [`docs/specs/host-level-tool.md`](../specs/host-level-tool.md)
**Issue:** [#286](https://github.com/wphillipmoore/standard-tooling/issues/286)
**Pushback review:**
[`paad/pushback-reviews/2026-04-24-host-level-tool-pushback.md`](../../paad/pushback-reviews/2026-04-24-host-level-tool-pushback.md)
**Last updated:** 2026-04-25

## Scope

This plan covers implementation of the host-level-tool distribution
model as defined in the spec. Work spans four repositories
(`standard-tooling`, `standard-tooling-docker`, `standard-actions`,
and each consumer) plus a docs sweep, sequenced in seven phases:

1. Code work in `standard-tooling` (move checks, env-var gate, delete
   the old hook).
2. Cut a `standard-tooling` release that makes the new behavior
   available to consumers.
3. `standard-tooling-docker`: pin image build to rolling tag, wire
   release-triggered rebuild.
4. `standard-actions`: update `standards-compliance` (and any
   sibling composites) to stop cloning `standard-tooling` and
   instead use the dev container or `uv sync --group dev`.
5. Python consumer migration (`ai-research-methodology`).
6. Non-Python consumer migration (plugin, docker repo's own consumer
   role, docs, standards repo).
7. Docs sweep and plugin error-message update.

Each phase has observable completion criteria. The plan assumes the
fleet-of-one operational model: producer and consumer are the same
person, fail-forward is the default rollback strategy.

## Out of scope for this plan

- **Consumer lockfile-bump automation** (dependabot / renovate /
  scheduled refresh PRs). Spec defers; if the manual cadence
  becomes friction, file a follow-up.
- **A pure-devcontainer install model.** Rejected in the spec under
  "Host install vs devcontainer-only" tradeoff.
- **Publishing `standard-tooling` to PyPI.** Explicitly rejected.
- **Re-introducing `[tool.uv.sources]` for non-Python repos.**
  Architecturally impossible (no `pyproject.toml`); the spec's
  whole point is that non-Python repos consume via the image.

## Phase 1: Code work in `standard-tooling`

**Goal:** This repo no longer ships an `st-pre-commit-hook` entry
point or a `scripts/lib/git-hooks/` directory. All commit-context
checks live in `st-commit`. The new env-var-plus-`GIT_REFLOG_ACTION`
gate is in `.githooks/pre-commit` and `core.hooksPath` is rewired to
point at it.

### Task 1.1: Move the five checks from `pre_commit_hook.py` into `commit.py`

**Requirement:** Spec "Migration / standard-tooling itself" step 1;
six-principle item 5 (single source of truth for commit-context
policy lives in `st-commit`).

#### RED — write ten failing tests in `tests/standard_tooling/test_commit.py`

For each of the five checks, write one rejection-path test and one
happy-path test:

1. **Detached HEAD:** monkeypatch `git.current_branch()` → `"HEAD"`;
   assert `commit.main()` returns non-zero with `"detached HEAD"`
   in stderr. Happy path: any normal branch name passes the check.
2. **Protected branches:** monkeypatch → `"develop"` (and
   `"release"`, `"main"`); assert non-zero with
   `"direct commits ... forbidden"`. Happy path: `"feature/42-x"`
   passes.
3. **Branch prefix:** monkeypatch → `"random-name"` with
   `repo_profile.branching_model = "library-release"`; assert
   non-zero with `"must use ... feature/*, bugfix/*, ..."`. Happy
   path: `"feature/42-x"` matches the model's regex and passes.
4. **Issue number:** monkeypatch → `"feature/no-number"`; assert
   non-zero with `"must include a repo issue number"`. Happy path:
   `"feature/42-x"` passes.
5. **Worktree convention:** in a tmp repo with `.worktrees/` and
   `git.is_main_worktree()` returning True, monkeypatch →
   `"feature/42-test"`; assert non-zero with
   `"feature-branch commits from the main worktree are forbidden"`.
   Happy path: same branch from a secondary worktree passes.

**Expected failure:** All ten tests fail because `commit.py`
currently has no validation logic — `main()` goes straight from
arg parsing to `git.has_staged_changes()`.

**If any pass unexpectedly:** validation has been partially moved
(e.g., a stray earlier commit). `git diff src/standard_tooling/bin/commit.py`
to see what's already there; adjust scope rather than add duplicate
logic.

#### GREEN — port each check from `pre_commit_hook.py` verbatim

Add a `_validate_commit_context(root: Path) -> int` helper at the
top of `commit.py`, and call it first in `main()` (before
`git.has_staged_changes()`). Lift the constants
(`_PROTECTED_BRANCHES`, `_BRANCHING_MODELS`, `_ISSUE_REQUIRED_RE`,
`_ISSUE_FORMAT_RE`, `_WORKTREE_SCOPED_RE`, `_WORKTREES_DIRNAME`)
verbatim from `pre_commit_hook.py`. The five checks return 1 with
the same `print(... file=sys.stderr)` patterns; helper returns 0
when all pass; `main()` propagates the non-zero return.

**Constraints:**

- Byte-identical behavior to the existing hook. The existing
  `tests/standard_tooling/test_pre_commit_hook.py` is the spec for
  this — a green run there (post-migration, before its deletion in
  Task 1.4) is the reference.
- Don't introduce exceptions for control flow. Preserve the
  print-and-return-1 pattern.
- No premature consolidation of the five `print/return` blocks —
  REFACTOR will decide.

#### REFACTOR

Run `pytest` in green state. Then look for:

- **Duplicated constants/regexes** between `pre_commit_hook.py`
  (still present until Task 1.4) and `commit.py`. If Task 1.4 lands
  in the same PR (it should), skip extraction — the duplication
  vanishes when the hook file is deleted. If 1.4 is split across
  PRs, promote shared symbols to a new `lib/branch_rules.py`.
- **The `print/return 1` boilerplate.** Five blocks share the
  shape `print(REASON, file=sys.stderr); print(HINT, file=sys.stderr);
  return 1`. A small `_reject(reason: str, hint: str) -> int`
  helper would tighten it. Apply only if the diff makes
  `commit.py` shorter on net.
- **Naming.** `_validate_commit_context` is fine; verify it doesn't
  shadow an existing name in the module.

### Task 1.2: Have `st-commit` set `ST_COMMIT_CONTEXT=1`

**Requirement:** Spec "Migration / standard-tooling itself" step 2;
"Consequences" subsection: "`st-commit` must always set
`ST_COMMIT_CONTEXT=1` before calling `git commit`. A unit test
pinning this behavior is a requirement of the migration —
forgetting it in a future refactor would break every commit
fleet-wide."

#### RED — write a failing test pinning the env-var contract

In `tests/standard_tooling/test_commit.py`, add a test that:

- Calls `monkeypatch.delenv("ST_COMMIT_CONTEXT", raising=False)` to
  start from a known-clean state.
- Monkeypatches `standard_tooling.bin.commit.git.run` with a
  callable that captures `os.environ.get("ST_COMMIT_CONTEXT")` at
  the moment of invocation.
- Drives `commit.main()` past validation (use the happy-path
  monkeypatches from Task 1.1's tests) and past
  `has_staged_changes` (return True).
- Asserts the captured value is `"1"` (string, not the integer or
  bool).

**Expected failure:** Captured value is `None` — `commit.py` does
not yet set the env var.

**If it passes unexpectedly:** the test runner inherited
`ST_COMMIT_CONTEXT=1` from the developer's shell. The
`monkeypatch.delenv` call should prevent this; if it's still
passing, the test is wrong (asserting against inherited
environment) — fix the test before claiming green.

#### GREEN — set the env var immediately before `git.run("commit", ...)`

In `commit.py`'s `main()`, just before
`git.run("commit", "--file", tmp_path)`:

```python
os.environ["ST_COMMIT_CONTEXT"] = "1"
```

Add `import os` at the top if not already imported.

**Constraints:**

- Mutate `os.environ` directly. The subprocess started by
  `git.run` inherits the parent process environment by default;
  no per-call env handling needed.
- Don't unset the var after the call — the process is exiting.
- Don't make this conditional on success of validation; by the
  time we reach the `git.run` call, all five checks have passed,
  so the env var is set unconditionally at that point.

#### REFACTOR

- `grep -rn ST_COMMIT_CONTEXT src/` — should match exactly one
  Python source location (this `os.environ` line). Document the
  contract via a short inline comment naming
  `.githooks/pre-commit` as the consumer of the signal.
- Consider promoting `"ST_COMMIT_CONTEXT"` and `"1"` to module
  constants. **Skip this** — the only Python-side reference is
  this single line, and the bash gate doesn't share constants
  across language boundaries. Premature.

### Task 1.3: Add `.githooks/pre-commit` (the new gate)

**Requirement:** Spec "Migration / standard-tooling itself" step 4;
"Decision: `st-commit` is the enforcement point; the hook is a
gate."

#### RED — write a shell-driven test exercising the gate's three branches

In a new file `tests/standard_tooling/test_pre_commit_gate.py`,
write three pytest tests that invoke the gate script directly via
`subprocess.run(["bash", str(GATE_PATH)], env=...)`:

1. **Admit by env var:** `env={"ST_COMMIT_CONTEXT": "1", "PATH":
   os.environ["PATH"]}`. Assert `returncode == 0`, empty stderr.
2. **Admit by `GIT_REFLOG_ACTION`:** parametrized over each
   admitted value — `"amend"`, `"cherry-pick"`, `"revert"`,
   `"rebase -i"`, `"rebase --continue"`, `"merge develop"`. Assert
   each yields `returncode == 0`.
3. **Reject:** `env={"PATH": os.environ["PATH"]}` (no
   `ST_COMMIT_CONTEXT`, no `GIT_REFLOG_ACTION`). Assert
   `returncode == 1`; assert stderr contains
   `"raw 'git commit' is blocked"`.

If `GATE_PATH = REPO_ROOT / ".githooks" / "pre-commit"` does not
exist, mark the tests as `pytest.skip` with reason
`"gate not yet implemented (RED phase)"` — that is the RED state.

**Expected failure:** All three tests skip (gate file absent).

**If they pass unexpectedly:** the file already exists from a
partial earlier commit. Verify `git ls-files .githooks/` and
either complete Task 1.3 or remove duplicate work.

#### GREEN — write the gate file

Create `.githooks/pre-commit` with the bash from the spec's
"Decision" section, byte-identical:

```bash
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

`chmod +x .githooks/pre-commit`. Re-run the tests; the three
tests should now pass instead of skip.

**Constraints:**

- Match the spec's bash byte-for-byte. A future spec/plan diff
  must be straightforward to read.
- No clever bash. No POSIX-only rewrites — bash 4+ is fine; this
  hook runs on developer machines with current bash.

#### REFACTOR

- `shellcheck .githooks/pre-commit` exits 0. The repo's validation
  pipeline catches this anyway, but verify here for fast feedback.
- If the test file has copy-paste of the env-construction
  boilerplate, factor a `_run_gate(env: dict) -> CompletedProcess`
  helper.
- The gate references `docs/repository-standards.md` as the
  pointer doc. Once `standard-tooling-plugin#87` lands a structured
  config (`st-config.{yml,toml}`), this URL will need updating;
  leave a `# TODO(plugin#87): point at st-config doc` comment in
  the bash file as a tombstone for that follow-up.

#### Manual sanity checks (out-of-test verification)

After the test suite is green:

- `git config core.hooksPath .githooks` then attempt a raw
  `git commit -m "test"` — rejected with the gate's error.
- `git commit --amend --no-edit` — admitted (`GIT_REFLOG_ACTION`
  is `amend`).
- `st-commit --type test --message "test" --agent claude`
    after staging a change — admitted (`ST_COMMIT_CONTEXT=1`).

### Task 1.4: Delete the old hook artifacts

- **Action:**
  - `git rm src/standard_tooling/bin/pre_commit_hook.py`
  - Remove the `st-pre-commit-hook` line from `[project.scripts]` in
    `pyproject.toml`.
  - `git rm scripts/lib/git-hooks/pre-commit` (and remove the empty
    `scripts/lib/git-hooks/` directory if it becomes empty —
    `rmdir scripts/lib/git-hooks` succeeds).
  - Delete `tests/standard_tooling/test_pre_commit_hook.py` (or rename and gut to
    cover the moved logic — depends on whether the new tests in 1.1
    duplicate or extend it; prefer the rename + gut path to preserve
    git history).
- **Verification:**
  - `find . -name pre_commit_hook.py -not -path './.venv/*'` returns
    nothing (top-level repo, not the venv).
  - `grep -n st-pre-commit-hook pyproject.toml` returns nothing.
  - `git status` shows the deletions staged.
  - `uv pip install -e .` rebuilds without the entry point.

### Task 1.5: Rewire this repo's `core.hooksPath`

- **Action:** Update this repo's local `core.hooksPath` setting:
  `git config core.hooksPath .githooks`. Update CLAUDE.md and
  README.md instructions to reference `.githooks` instead of
  `scripts/lib/git-hooks` (this is part of Phase 7's broader sweep,
  but doing it now keeps this repo consistent at every commit).
- **Verification:** `git config --get core.hooksPath` returns
  `.githooks`. Raw `git commit` is rejected by the new gate.

### Task 1.6: Validate the full pipeline locally

- **Action:** Run `st-docker-run -- uv run st-validate-local`
  inside the worktree. Confirm tests pass, lint passes, typecheck
  passes.
- **Verification:** `st-validate-local` exits 0.
- **Sub-check — dev-tree override survives the changes.** From the
  main worktree:

  ```bash
  UV_PROJECT_ENVIRONMENT=.venv-host uv sync --group dev
  PATH="$PWD/.venv-host/bin:$PATH" which st-docker-run    # → .venv-host/bin/...
  PATH="$PWD/.venv-host/bin:$PATH" st-docker-run --help   # → exits 0
  ```

  Confirms Principle 4 from the spec (dev-tree override via PATH
  ordering against `.venv-host`) still works after the Phase 1
  code changes. Nothing in Phase 1 should break this, but verifying
  closes the loop on the pushback resolution that restored
  `.venv-host`.

### Task 1.7: Open the PR, get it merged, `st-finalize-repo`

- **Action:** Standard PR workflow. PR body references #286,
  summarizes the consolidation, and lists the deleted entry point so
  reviewers (future-you) understand the surface change.
- **Verification:** PR merged to `develop`; `st-finalize-repo` run.

**Phase 1 exit criteria:** `pre_commit_hook.py` deleted, new gate
in place, this repo passes its own validation, PR merged.

## Phase 2: Cut a `standard-tooling` release

**Goal:** Consumers can pin to a tagged version that contains the
new behavior. Without a release, the rolling minor tag points at
old code and consumers cannot adopt.

### Task 2.1: Bump version, prepare release

- **Action:** Cut `v1.3.0`. The `pyproject.toml` version is already
  at `1.3.0`; confirm `st-prepare-release` produces a release branch
  and changelog targeting that version.
- **Release-notes content:** Call out the `st-pre-commit-hook`
  entry-point removal as a clean break. Strictly this is a public-
  API change that would warrant `v2.0.0`, but no in-fleet consumer
  invokes the entry point directly (all wire `core.hooksPath` at
  `scripts/lib/git-hooks/pre-commit`, which is also being deleted).
  Documenting the removal in the release notes is the cost of the
  fleet-of-one fail-forward stance.
- **Verification:** Release branch + PR opened; PR title reflects
  `v1.3.0`; release notes mention the entry-point removal.

### Task 2.2: Merge release PR; tags published

- **Action:** Merge release PR. `tag-and-release` composite creates
  `v1.3.0`, force-updates rolling minor tag to `v1.3`.
- **Verification:**
  - `git ls-remote --tags origin | grep -E 'v1\.3'` shows
    `v1.3.0` and `v1.3`.
  - GitHub Release for `v1.3.0` exists.

### Task 2.3: Confirm consumers can install the new version

- **Action:** On a clean shell, run
  `uv tool install 'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.3'`.
  Verify `st-commit` is on `PATH` and rejects malformed branches /
  raw `git commit`.
- **Verification:** Sanity-check transcript captured (or just
  validated mentally — fleet-of-one).

**Phase 2 exit criteria:** `v1.3.0` released; rolling `v1.3` tag
exists; install from the rolling tag yields the new behavior.

## Phase 3: `standard-tooling-docker` — image policy

**Goal:** Dev container images stop drifting against
`standard-tooling`. Each `standard-tooling` release triggers a
rebuild that produces images carrying the released version.

This phase is owned by `standard-tooling-docker#51` and the work
happens in that repo. The plan items below are the scope this spec
imposes on that issue.

### Task 3.1: Switch pre-bake to pin the rolling minor tag

- **Action:** In
  `standard-tooling-docker/docker/common/standard-tooling-uv.dockerfile`,
  replace:

  ```dockerfile
  RUN git clone --depth 1 -b develop https://github.com/wphillipmoore/standard-tooling.git /tmp/standard-tooling \
      && uv pip install --system /tmp/standard-tooling \
      && rm -rf /tmp/standard-tooling
  ```

  with:

  ```dockerfile
  RUN pip install --no-cache-dir \
      'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.3'
  ```

  Bump the pin tag (`v1.3` here, future minors later) when the
  publisher decides consumers should opt in to a new minor.
- **Verification:** Local image build succeeds; inside the container,
  `st-validate-local --version` (if available; otherwise
  `pip show standard-tooling`) reports `v1.3.x`.

### Task 3.2: Wire release-triggered rebuild

- **Action:** In `standard-tooling-docker`, add a workflow listening
  on `repository_dispatch` (event type: `standard-tooling-released`
  or similar). The workflow rebuilds and publishes the dev images.
  Mirror with a workflow change in `standard-tooling`'s release
  pipeline that fires the dispatch event after `tag-and-release`
  completes.
- **Verification:**
  - Manually trigger the dispatch (`gh api -X POST
    /repos/wphillipmoore/standard-tooling-docker/dispatches -f
    event_type=standard-tooling-released`); confirm the rebuild
    workflow runs.
  - Cut a `standard-tooling` patch release and confirm the
    standard-tooling-docker workflow fires automatically.

### Task 3.3: Verify image freshness post-rebuild

- **Action:** After Phase 2's release and Phase 3 wiring lands,
  pull the latest `dev-base` (or `dev-python`) image and confirm
  it carries `standard-tooling v1.3.x`.
- **Verification:**

  ```bash
  docker pull ghcr.io/wphillipmoore/dev-base:latest
  docker run --rm ghcr.io/wphillipmoore/dev-base:latest \
      pip show standard-tooling | grep Version
  ```

  reports `v1.3.x`.

**Phase 3 exit criteria:** Dockerfile pinned to rolling tag; release
dispatch wired; freshly-rebuilt images carry the released version.

## Phase 4: `standards-compliance` — stop cloning `standard-tooling`

**Goal:** The `standards-compliance` composite action (and any
sibling composite that bootstraps `standard-tooling` onto the
runner) stops cloning the repo and adding `scripts/bin/` to `PATH`.
That `scripts/bin/` directory no longer exists, and the spec's
position is that CI uses one of the two existing distribution paths.

This phase is owned by a new issue to be filed against
`standard-actions`.

### Task 4.1: File the `standard-actions` issue

- **Action:** File an issue in `wphillipmoore/standard-actions`
  describing the work: replace the clone-and-PATH-prepend pattern
  in `actions/standards-compliance/action.yml` with one of:
  - For Python repos: rely on the consumer's own `uv sync --group
    dev` step (if the action runs after that step, no install is
    needed).
  - For non-Python repos: run the action's steps inside the dev
    container image (`jobs.<name>.container:` or invoke
    `st-docker-run` from the runner). The image's pre-baked
    `standard-tooling` is on `PATH`.
  Reference this spec and #286.
- **Verification:** Issue filed, linked from #286.

### Task 4.2: Implement and merge

- **Action:** Per the new issue's scope. PR against `standard-actions`.
- **Verification:** Updated `standards-compliance` runs green
  against at least one Python consumer (`ai-research-methodology`)
  and one non-Python consumer (e.g., `standard-tooling-plugin`).

### Task 4.3: Audit other composites

- **Action:** `grep -r "standard-tooling" actions/` in
  `standard-actions`. For each composite that clones or PATH-pre-
  pends, apply the same fix or document why it doesn't apply.
- **Verification:** `grep` returns no actions cloning
  `standard-tooling`; remaining references are documentation only.

**Phase 4 exit criteria:** `standards-compliance` no longer clones
`standard-tooling`; CI in both Python and non-Python consumers runs
green against the updated action.

## Phase 5: Python consumer migration

**Goal:** Every Python consumer declares `standard-tooling` as a
dev dep, drops sibling-checkout wiring, and vendors the new gate.

### Task 5.1: `ai-research-methodology`

- **Action:**
  1. Add to `pyproject.toml`:

     ```toml
     [dependency-groups]
     dev = [
         "standard-tooling",
         # … other dev deps …
     ]
     [tool.uv.sources]
     standard-tooling = { git = "https://github.com/wphillipmoore/standard-tooling", tag = "v1.3" }
     ```

  2. `uv sync --group dev`; commit `pyproject.toml` + `uv.lock`.
  3. Vendor `.githooks/pre-commit` (the env-var-plus-
     `GIT_REFLOG_ACTION` gate, copied verbatim from the spec).
     `chmod +x .githooks/pre-commit`.
  4. Update repo's `core.hooksPath` instructions in CLAUDE.md /
     README to point at `.githooks` instead of
     `../standard-tooling/scripts/lib/git-hooks`.
  5. Remove `.venv-host` references and any sibling-checkout
     bootstrap from CLAUDE.md / docs / `scripts/`.
- **Verification:**
  - Fresh clone: `git config core.hooksPath .githooks && uv sync
    --group dev && st-docker-run -- uv run st-validate-local` runs
    green.
  - Raw `git commit -m "test"` is refused.
  - `git commit --amend --no-edit` is admitted.

### Task 5.2: Other Python consumers

- **Action:** Apply the same five-step change to
  `mq-rest-admin-python` when it re-enters active development. Not
  required to land in this implementation cycle since the repo is
  currently dormant.
- **Verification:** Tracked under #288.

**Phase 5 exit criteria:** `ai-research-methodology` migrated; CI
green; sibling-checkout references removed.

## Phase 6: Non-Python consumer migration

**Goal:** Every non-Python consumer vendors the new gate and drops
sibling-checkout wiring. They rely on the dev container image's
pre-bake (which Phase 3 now keeps fresh).

### Task 6.1: `standard-tooling-plugin`

- **Action:**
  1. Vendor `.githooks/pre-commit`. `chmod +x`.
  2. Update repo's `core.hooksPath` instructions.
  3. Remove sibling-checkout / `.venv-host` references from CLAUDE.md
     and docs.
  4. **Phase 7 link:** update `hooks/scripts/validate-on-edit.sh`'s
     error-message URL from the sibling-checkout bootstrap guide to
     the new spec / getting-started doc. (Tracked under Phase 7
     Task 7.3 if not done here.)
- **Verification:**
  - Fresh clone, set `core.hooksPath`, raw `git commit` refused.
  - Plugin's PostToolUse hook still fires correctly.
  - **Image pre-bake provenance check** (matches spec verification
    language for non-Python consumers):

    ```bash
    st-docker-run -- which st-validate-local    # → /usr/local/bin/... (image pre-bake)
    st-docker-run -- pip show standard-tooling  # → Version: v1.3.x
    ```

    Confirms `st-*` inside the container comes from the image and
    that the image is current — catches the silent-stale-image
    failure mode that motivated `standard-tooling-docker#51`.

### Task 6.2: `standard-tooling-docker` (consumer role)

- **Action:** Same gate-vendor + sibling-checkout cleanup as 6.1.
  This is separate from the Phase 3 work — that was the repo
  *publishing* the images; this is the repo *using* `st-*` in its
  own dev workflow.
- **Verification:** Same as 6.1, including the image-pre-bake
  provenance check.

### Task 6.3: `the-infrastructure-mindset`

- **Action:** Same gate-vendor + sibling-checkout cleanup as 6.1.
- **Verification:** Same as 6.1, including the image-pre-bake
  provenance check.

### Task 6.4: `standards-and-conventions`

- **Action:** Same gate-vendor + sibling-checkout cleanup as 6.1.
- **Verification:** Same as 6.1, including the image-pre-bake
  provenance check.

### Task 6.5: `mq-rest-admin-*` non-Python variants (deferred)

- **Action:** Same gate-vendor + cleanup. Apply when each variant
  re-enters active development. Tracked under #288.
- **Verification:** Per-variant when each lands.

**Phase 6 exit criteria:** All currently active non-Python
consumers migrated; CI green; sibling-checkout references removed.

## Phase 7: Docs sweep and plugin error-message update

**Goal:** No stale references to `scripts/lib/git-hooks`,
`../standard-tooling/.venv-host/bin`, or sibling-checkout patterns
remain anywhere in the fleet's documentation.

This phase is the substance of #288.

### Task 7.1: `standard-tooling`'s own docs

- **Action:** Sweep this repo:

  ```bash
  grep -rln "scripts/lib/git-hooks\|\.venv-host/bin\|\.\./standard-tooling/" CLAUDE.md README.md docs/
  ```

  For each match, rewrite to use the new gate / `.githooks/` /
  host-level install model.
- **Verification:** The grep above returns zero matches.

### Task 7.2: Each consumer repo's docs

- **Action:** Same grep + sweep in every consumer repo touched in
  Phases 5–6. Each repo's CLAUDE.md gets its own rewrite to match
  the new model.
- **Verification:** Per-repo grep returns zero matches.

### Task 7.3: Plugin `validate-on-edit.sh` error message

- **Action:** Update
  `standard-tooling-plugin/hooks/scripts/validate-on-edit.sh`'s
  `additionalContext` string to reference the new install path
  (`uv tool install ...`) and the new spec / getting-started doc.
- **Verification:** Trigger the failure mode (rename `st-docker-run`
  off `PATH` temporarily); confirm the error message points at the
  new doc.

### Task 7.4: Update `docs/specs/git-url-dev-dependency.md`

- **Action:** Delete the file. The pushback report
  (`paad/pushback-reviews/2026-04-24-git-url-dev-dependency-pushback.md`)
  preserves the rejection record; the file itself is no longer
  needed.
- **Verification:** `git rm docs/specs/git-url-dev-dependency.md`;
  the references-from list in `host-level-tool.md` updated to drop
  the broken link.

### Task 7.5: Rewrite the canonical getting-started narrative

- **Action:** In `docs/site/docs/getting-started.md` (and any
  consumer repo equivalent), replace the install / bootstrap
  section with the four-step flow from the spec's
  [First-time developer setup](../specs/host-level-tool.md#first-time-developer-setup)
  section: install `uv` → `uv tool install standard-tooling` →
  confirm → per-repo `core.hooksPath` + `uv sync --group dev`
  (Python only). This is a **narrative rewrite**, not a
  find-and-replace — the doc must read as a coherent install
  walkthrough for a new developer, not a patchwork of edited
  paragraphs.
- **Verification:** A fresh reader following the doc top-to-bottom
  on a clean machine ends with `st-docker-run --help` working and
  the new repo's `.githooks/pre-commit` enforcement active. Spec
  acceptance line "Getting-started docs updated to the four-step
  flow" can be checked.

**Phase 7 exit criteria:** Fleet-wide grep for the legacy patterns
returns zero matches **and** the canonical getting-started narrative
reflects the four-step flow.

## Closeout

### Task 8.1: Close #286

- **Action:** Verify all spec acceptance criteria are checked.
  Close #286 with a comment linking to the spec, plan, and
  pushback report.
- **Verification:** #286 closed.

### Task 8.2: Close / update related issues

- **Action:**
  - Close `standard-tooling-docker#51` (resolved by Phase 3).
  - Close the `standard-actions` issue from Task 4.1 (resolved by
    Phase 4).
  - Update #288 (docs sweep) to reflect actual completion (most of
    its work happens in Phase 7).
- **Verification:** Issue states match reality.

## Dependencies and blockers

| Depends on | Blocks | Notes |
|------------|--------|-------|
| Phase 1 complete | Phase 2 (release) | Can't release without the code |
| Phase 2 complete | Phases 3, 5, 6 | Consumers and image pin can't reference a tag that doesn't exist yet |
| Phase 3 complete | Phase 6 | Non-Python consumers depend on fresh images |
| Phase 4 complete | Phase 6 (CI) | Non-Python CI breaks until `standards-compliance` updated |
| Phases 5 + 6 + 4 | Phase 7 | Docs sweep can lag the migration but should not lead it |

Phases 3, 4, 5 can run in parallel after Phase 2; only the
respective Phase 6 sub-tasks are gated by their predecessors.

## Success criteria (aggregated, mapped to spec acceptance criteria)

- [x] Spec drafted and pushback-reviewed (complete; see
  pushback report)
- [ ] `paad:alignment` run between this plan and the spec
  (next paad step)
- [ ] Phase 1 complete: `pre_commit_hook.py` deleted, env-var gate
  in place, repo self-validates
- [ ] Phase 2 complete: `v1.3.0` released; rolling `v1.3` tag
  exists
- [ ] Phase 3 complete: `standard-tooling-docker` pins rolling tag;
  release dispatch wired; rebuilt images carry released version
- [ ] Phase 4 complete: `standards-compliance` no longer clones
  `standard-tooling`; CI green for both Python and non-Python
  consumers
- [ ] Phase 5 complete: `ai-research-methodology` declares dev dep,
  vendors gate, removes sibling-checkout refs
- [ ] Phase 6 complete: plugin / docker repo / docs / standards
  repo each vendor gate, remove sibling-checkout refs
- [ ] Phase 7 complete: fleet-wide grep returns zero stale
  references
- [ ] #286, `standard-tooling-docker#51`, and the new
  `standard-actions` issue closed; #288 updated
