# Alignment Review: standard-tooling.toml migration

**Date:** 2026-04-29
**Commit:** 50d59b6cac3ad48fdbaf043f0a106ef7970b0b6a

## Documents Reviewed

- **Intent:** `docs/specs/standard-tooling-toml.md` (spec for issue #363)
- **Action:** `docs/plans/standard-tooling-toml-plan.md` (Phase 2 implementation plan)
- **Design:** none (spec includes implementation design inline)

## Source Control Conflicts

None — no conflicts with recent changes.

## Issues Reviewed

### [1] Spec doesn't account for ConfigError propagation to consumers
- **Category:** missing coverage
- **Severity:** important
- **Documents:** Spec "Consumer migration" section
- **Issue:** The spec prescribed replacing `read_profile()` with
  `read_config()` in three consumers, but `read_config()` can raise
  `ConfigError` for validation failures (malformed TOML, invalid enum,
  bad trailer format) — an exception type `read_profile()` never
  raised. Consumers need to handle it. The plan already included the
  handling; the spec did not mention it.
- **Resolution:** Added "Handle `ConfigError` from validation failures
  (exit with diagnostic)" to each consumer migration bullet in the
  spec.

### [2] Plan strips "Validation policy" section but spec only names two sections
- **Category:** scope compliance
- **Severity:** minor
- **Documents:** Spec "Context" paragraph, Plan Task 10
- **Issue:** The spec said config sections "repository profile, AI
  co-authors" are stripped. The plan also stripped "Validation policy"
  (containing dropped fields `canonical_local_validation_command` and
  `validation_required`). Consistent with the spec's "Dropped fields"
  list but not explicitly named.
- **Resolution:** Updated the spec to name all three sections:
  "repository profile, AI co-authors, validation policy."

## Unresolved Issues

None — all issues addressed.

## Alignment Summary

- **Requirements:** 20 total, 20 covered, 0 gaps
- **Tasks:** 10 total, 10 in scope, 0 orphaned
- **Design items:** N/A (no separate design doc)
- **Status:** Aligned — ready for implementation
