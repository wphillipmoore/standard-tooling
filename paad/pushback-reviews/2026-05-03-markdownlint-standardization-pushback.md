# Pushback Review: Standardize markdownlint configuration across the fleet

**Date:** 2026-05-03
**Spec:** docs/specs/2026-05-03-markdownlint-standardization-design.md
**Commit:** ff993c74da2728372164ef4eb9a0c41450064b55

## Source Control Conflicts

None — no conflicts with recent changes. The spec accurately describes
the current state of `validate_local_common_container.py` and the
`st-markdown-standards` entry point. Recent commit `c1133c4` (remove
markdownlint shutil.which guard) is consistent with the spec's direction.

## Scope Shape

Single cohesive initiative, no split needed. In-repo code change is
small; fleet sweep is mechanical. Reasonable as one spec.

## Issues Reviewed

### [1] Empty ignore file will lint vendored and generated content

- **Category:** omission
- **Severity:** critical
- **Issue:** `markdownlint` does not respect `.gitignore`. The spec
  bundled an empty `.markdownlintignore` and runs `markdownlint .`,
  which would lint `.venv/`, `.venv-host/`, `node_modules/`,
  `.worktrees/`, `CHANGELOG.md`, and `releases/`. The current
  `releases/.markdownlint.json` disables 8 rules, confirming that
  content cannot pass the standard config. The current
  `.markdownlintignore` excludes `CHANGELOG.md` and `releases/`,
  but those exemptions may have been agent drift rather than
  deliberate decisions.
- **Resolution:** Populate the bundled ignore file with
  vendored/build/duplicate paths (`.venv/`, `.venv-host/`,
  `node_modules/`, `.worktrees/`). Generated content (`CHANGELOG.md`,
  `releases/`) stays in scope — fix the generators rather than
  permanently exempting output. Philosophy is "global by default,
  shrink back as needed": exceptions added only when a path proves
  non-conformable after reasonable effort. Spec updated.

### [2] Scope expansion blast radius unacknowledged

- **Category:** scope imbalance
- **Severity:** serious
- **Issue:** The switch from `docs/site/**/*.md` + `README.md` to
  `markdownlint .` is a fundamental change in lint philosophy, but
  the spec treated it as a one-liner. Every `.md` file in every
  repo — specs, plans, design docs, `CLAUDE.md`, AI-generated
  review outputs — would be linted for the first time. The fleet
  cleanup section said "fix lint violations" without estimating
  the blast radius.
- **Resolution:** Spec updated to acknowledge the blast radius and
  recommend ordering the fleet sweep from least to most
  markdown-heavy repos to surface issues incrementally. Universal
  scope stays — the cleanup is finite.

### [3] `releases/.markdownlint.json` directory-level override

- **Category:** feasibility
- **Severity:** moderate
- **Issue:** The spec said "delete local markdownlint configs" but
  didn't address the `releases/.markdownlint.json` directory-level
  override. This override disables 8 rules because release notes
  (sourced from GitHub Releases API data) don't conform. With
  `--config` pointing at the bundled config, markdownlint-cli
  ignores directory-level overrides, so strict rules would apply
  to `releases/` content.
- **Resolution:** Consistent with issue 1: try global scope first.
  If release note generators can produce compliant output, the
  override was unnecessary. If not, `releases/` gets added to the
  bundled ignore file after the attempt. Per-repo cleanup updated
  to include deleting `releases/.markdownlint.json`. Spec updated.

### [4] `st-markdown-standards` removal ordering (withdrawn)

- **Category:** feasibility
- **Severity:** minor
- **Issue:** Initially flagged a potential ordering concern between
  removing `st-markdown-standards` and updating consuming repos.
  On closer inspection, the ordering holds: `st-markdown-standards`
  is genuinely internal, and `standard-tooling-docker`'s standalone
  CI job is in its own CI pipeline, not in consuming repos.
- **Resolution:** Withdrawn — non-issue. Additionally noted: this
  is a scale-of-one project with no external users. The spec
  designs for proper staged deployment (so the patterns are ready
  when users arrive) but execution can skip deprecation cycles and
  transition windows in the interest of moving fast.

### [5] Global linting scope is not worth the complexity (post-merge re-evaluation)

- **Category:** scope imbalance
- **Severity:** serious
- **Issue:** After merging the initial spec, the author questioned
  whether linting all markdown files delivers any real return on
  investment. The config standardization (bundled canonical rules,
  delete per-repo configs) solves the original problem — config drift
  causing identical content to pass in one repo and fail in another.
  The scope expansion from `docs/site/ + README.md` to `markdownlint .`
  was responsible for nearly every complication addressed in issues
  1-3: vendored-path exclusions, generator compliance, blast radius,
  directory-level override migration. Internal working documents
  (specs, plans, design docs) are not user-facing and gain no value
  from markdownlint enforcement.
- **Resolution:** Reverted scope to the original `docs/site/**/*.md`
  + `README.md`. The ignore file, "global by default" philosophy,
  blast radius note, and generator compliance concerns were all
  removed. Config standardization and stale config hygiene remain.
  Spec and plan updated.

## Summary

- **Issues found:** 5
- **Issues resolved:** 5 (1 withdrawn)
- **Unresolved:** 0
- **Spec status:** ready for implementation (scope narrowed, spec and plan updated)
