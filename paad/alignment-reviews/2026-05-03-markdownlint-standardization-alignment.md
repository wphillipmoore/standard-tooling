# Alignment Review: Standardize markdownlint configuration

**Date:** 2026-05-03
**Commit:** ff993c74da2728372164ef4eb9a0c41450064b55

## Documents Reviewed

- **Intent:** docs/specs/2026-05-03-markdownlint-standardization-design.md
- **Action:** docs/plans/2026-05-03-markdownlint-standardization.md
- **Design:** none (spec serves as both requirements and design)

## Source Control Conflicts

None — no conflicts with recent changes (covered in pushback review).

## Issues Reviewed

### [1] Plan "Out of scope" contradicts spec's "global by default" philosophy

- **Category:** missing coverage
- **Severity:** important
- **Documents:** Plan "Out of scope" vs spec "Canonical Config" philosophy
- **Issue:** The plan declared changelog generator fixes out of scope,
  but the spec (updated during pushback) says generated content stays
  in lint scope and generators should be fixed. This created a
  contradictory decision path for Step 5 / Phase 3 when generated
  files fail linting.
- **Resolution:** Removed the out-of-scope line about generators.
  The spec's "global by default, shrink back as needed" philosophy
  already covers the decision path — fix generators if possible,
  add to ignore file only after reasonable effort fails.

### [2] Package data config insufficient for new config files

- **Category:** missing coverage
- **Severity:** important
- **Documents:** Plan Step 1 vs pyproject.toml
- **Issue:** The plan said "verify [tool.setuptools.package-data]"
  but didn't flag that the current config (`data/*.json`) specifically
  cannot match `.yaml` or extensionless files in the new `configs/`
  directory. Missing this would cause `importlib.resources` to fail
  at runtime — a "works in dev, broken in install" bug.
- **Resolution:** Made the pyproject.toml update an explicit sub-step
  in Step 1 with the specific glob needed (`configs/*`).

### [3] Validator module docstring describes old behavior

- **Category:** missing coverage
- **Severity:** minor
- **Documents:** Plan Step 2 vs validate_local_common_container.py
- **Issue:** The module docstring says "markdownlint on published
  markdown (docs/site/, README.md)" which would be wrong after the
  change. The plan didn't mention updating it.
- **Resolution:** Added a note to Step 2 to update the docstring.

## Alignment Summary

- **Requirements:** 12 traced, 12 covered after fixes, 0 gaps
- **Tasks:** 10 total (7 phase-1 steps + release + fleet sweep + out
  of scope), 10 in scope, 0 orphaned
- **Status:** aligned (plan and spec updated)
