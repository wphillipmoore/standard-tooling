# Pushback Review: uv-tool-install-and-guard-cleanup-design

**Date:** 2026-05-01
**Spec:** `docs/specs/2026-04-30-uv-tool-install-and-guard-cleanup-design.md`
**Commit:** edb060a

## Source Control Conflicts

None — no conflicts with recent changes. The spec's assumptions about
file contents and line numbers matched the current codebase. Recent
commit `f4ea690` (use uv run for validation in Python repos during
finalization) already established the Python-vs-non-Python distinction
that the spec acknowledges.

## Scope Shape

**Cohesion:** The two features (pip-to-uv migration + guard cleanup)
serve different goals but are tightly connected by the same "just call
the tool" principle. No split recommended.

**Size:** Five targeted file changes, clear scope. Not oversized. Scope
expanded slightly during review to include error-handling corrections
and a warning-to-fatal audit (see Issues 3–5).

## Issues Reviewed

### [1] `_check_docs_workflow_status` gh guard removal — WITHDRAWN

- **Category:** Feasibility
- **Severity:** Critical (initially)
- **Issue:** Removing the `shutil.which("gh")` guard in
  `_check_docs_workflow_status` would cause `subprocess.run` to raise
  `FileNotFoundError` (a Python exception, not a process exit code),
  crashing finalize for a purely advisory check. The spec's claim that
  `result.returncode != 0` would catch this was incorrect.
- **Resolution:** Withdrawn. The user's position is that errors should
  be fatal, not advisory. The docs workflow check should never have
  been advisory — if `gh` is not present, the host install is broken
  and finalize should fail. The guard removal is correct; the advisory
  *caller* behavior also needs to change (see Issue 3).

### [2] `_ensure_tool("git-cliff")` call not mentioned

- **Category:** Omission
- **Severity:** Serious
- **Issue:** The spec said to remove `_ensure_tool` function and the
  `_ensure_tool("gh")` call, but `prepare_release.py:200` also calls
  `_ensure_tool("git-cliff")` in `_generate_changelog`. Removing the
  function without addressing this call would cause `NameError`.
- **Resolution:** Spec updated to explicitly mention removing both
  `_ensure_tool("gh")` (line 292) and `_ensure_tool("git-cliff")`
  (line 200).

### [3] Docs workflow failure must become fatal

- **Category:** Omission
- **Severity:** Serious
- **Issue:** The spec removed the `shutil.which("gh")` guard but
  didn't address the caller at `finalize_repo.py:290` which treats
  docs workflow failure as advisory (exit code 0, "soft warning"
  comment). After guard removal, a function that crashes on missing
  `gh` but exits 0 on actual workflow failure is inconsistent.
- **Resolution:** Spec updated: `_check_docs_workflow_status` failure
  returns exit 1. "Soft warning" comment and advisory framing removed.
  Principle 6 (errors are fatal) added to support this.

### [4] `_build_cached_image` silently falls back to base image

- **Category:** Scope imbalance
- **Severity:** Serious
- **Issue:** The spec changed the pip-to-uv line in
  `_build_cached_image` but didn't touch the error handling. Two
  fallback paths (lines 121-126 and 134-139) return the base image on
  failure, producing a container without `st-*` tools that causes
  confusing downstream "command not found" errors. Same
  catch-and-degrade anti-pattern the spec removes elsewhere.
- **Resolution:** Both failures made fatal — raise instead of
  returning base image. Added to spec section 1 and test strategy.

### [5] No architectural rule for error handling going forward

- **Category:** Omission
- **Severity:** Moderate
- **Issue:** The spec removed specific guard patterns but didn't
  establish the broader principle or require an audit. Without a stated
  rule, the next AI-generated PR will reintroduce the same pattern.
- **Resolution:** Principle 6 added: "Errors are fatal by default. Do
  not catch exceptions to downgrade them to warnings or silently fall
  back to a degraded path." Acceptance criterion added for a
  warning-to-fatal audit across `src/standard_tooling/`.

### [6] `pip install` not fully eliminated from docs

- **Category:** Contradiction
- **Severity:** Moderate
- **Issue:** The spec's section 5 listed three specific update points
  in `host-level-tool.md`, but `pip install` appears in many more
  places: the comparison table (lines 144-174), the "alternative"
  framing in the deployment targets table, the upgrade section's
  `pip install` command. The spec was under-scoped.
- **Resolution:** `pip install` is eliminated entirely. Section 5
  rewritten to remove all references, including the comparison table.
  `uv tool install` is the only documented install mechanism.
  Acceptance criterion added with grep verification.

### [7] Test strategy didn't cover new behavioral changes

- **Category:** Omission
- **Severity:** Moderate
- **Issue:** Test strategy listed three items but didn't cover the
  behavioral inversions added during review: `_build_cached_image`
  raising on failure, docs workflow failure becoming fatal,
  `_ensure_tool("git-cliff")` removal.
- **Resolution:** Three test items added to the test strategy section.

## Unresolved Issues

None — all issues addressed.

## Summary

- **Issues found:** 7
- **Issues resolved:** 7 (1 withdrawn, 6 accepted and applied)
- **Unresolved:** 0
- **Spec status:** Updated and ready for implementation.
- **Scope change:** Slightly expanded. Original scope was 5 file
  changes (pip-to-uv + guard removal). Final scope adds: fatal error
  handling in `_build_cached_image`, fatal docs workflow check, new
  principle 6 (errors are fatal), `pip install` doc sweep, and a
  warning-to-fatal audit across `src/standard_tooling/`.
