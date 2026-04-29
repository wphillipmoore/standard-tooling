# Pushback Review: standard-tooling.toml migration spec

**Date:** 2026-04-29
**Spec:** `docs/specs/standard-tooling-toml.md`
**Commit:** 50d59b6cac3ad48fdbaf043f0a106ef7970b0b6a

## Source Control Conflicts

None — no conflicts with recent changes. The #389 decomposition
(structural checks moved into `repo_profile_cli.py`) is consistent
with the spec's assumptions.

## Issues Reviewed

### [1] Phase 2 omits version-pin bumps in consuming repos
- **Category:** omission
- **Severity:** critical
- **Issue:** The original phasing had consuming repos strip their
  markdown config and add the TOML file in a single "flag-day"
  Phase 2. But consuming repos would still be running the old
  validator (pinned to their current standard-tooling version),
  which checks the markdown. Stripping markdown without bumping
  the version pin breaks CI.
- **Resolution:** Moot — resolved by reordering the phases. New
  approach: seed `standard-tooling.toml` across all repos first
  (harmless to the old validator), then ship the new reader as a
  1.4.x patch. Consuming repos pick up the new validator
  automatically via their floating `@v1.4` pin. Markdown cleanup
  happens last, after the new validator is active everywhere.

### [2] `docker_cache.py` cache-key migration not detailed
- **Category:** omission
- **Severity:** moderate
- **Issue:** The spec's retire-`st-config.toml` phase said to
  update `st-docker-run` but did not mention `docker_cache.py`,
  which hardcodes `"st-config.toml"` in `_CACHE_FILES` (lines
  19–24) and `_DEFAULT_CACHE_FILES` (line 25). When
  `st-config.toml` is deleted, the cache hash computation
  silently stops including the config file (the `is_file()` check
  filters it out), so config changes no longer invalidate the
  Docker image cache.
- **Resolution:** Added `docker_cache.py` explicitly to the
  retire phase (now Phase 4) with the specific change: replace
  `"st-config.toml"` with `"standard-tooling.toml"` in both
  dictionaries.

### [3] `versioning-scheme` enum has confusing `library` vs `semver` naming
- **Category:** ambiguity
- **Severity:** moderate
- **Issue:** Both `library` and `semver` appear as
  `versioning-scheme` values, but both are semantic versioning in
  practice. The distinction is unclear from the names alone, and
  the spec did not define what each value means.
- **Resolution:** Added one-line definitions for every enum value
  in the schema section. A follow-on issue will audit whether any
  values are functionally identical and should be collapsed after
  migration.

## Unresolved Issues

None — all issues addressed.

## Summary

- **Issues found:** 3
- **Issues resolved:** 3
- **Unresolved:** 0
- **Spec status:** Ready for implementation (updated in place)
