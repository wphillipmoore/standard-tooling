# Implementation Plan: Standardize markdownlint configuration

Spec: `docs/specs/2026-05-03-markdownlint-standardization-design.md`
Issue: https://github.com/wphillipmoore/standard-tooling/issues/476

## Phase 1: Validator changes (standard-tooling)

All work in the `issue-476-markdownlint-standardization` worktree.

### Step 1: Create the configs package

Create `src/standard_tooling/configs/` as a Python package with the
bundled config files:

- `src/standard_tooling/configs/__init__.py` (empty)
- `src/standard_tooling/configs/markdownlint.yaml` (canonical config)
- `src/standard_tooling/configs/markdownlintignore` (vendored paths)

Update `[tool.setuptools.package-data]` in `pyproject.toml` to include
the new config files. The current glob (`data/*.json`) does not match
`.yaml` or extensionless files. Add `configs/*` to the list so that
`importlib.resources` can resolve the bundled files at runtime.

### Step 2: Update `validate_local_common_container.py`

Replace the markdownlint section:

1. Update the module docstring to reflect the new scope (all
   repo-owned markdown via bundled config, not just `docs/site/`
   + `README.md`).
2. Remove `_find_markdown_files()` helper.
3. Replace the markdownlint invocation block with:
   - Resolve bundled config and ignore paths via `importlib.resources`.
   - Run `markdownlint --config <config> -p <ignore> .` from repo root.
4. Keep shellcheck and yamllint sections unchanged.

### Step 3: Remove `st-markdown-standards`

1. Delete `src/standard_tooling/bin/markdown_standards.py`.
2. Remove the `st-markdown-standards` entry from
   `pyproject.toml` `[project.scripts]`.
3. Delete `tests/standard_tooling/test_markdown_standards.py`.

### Step 4: Update tests for the common container validator

1. Remove `_find_markdown_files` from test imports.
2. Remove `test_find_markdown_files_*` test functions.
3. Add tests for the new markdownlint invocation:
   - Verify the command includes `--config` pointing to bundled config.
   - Verify the command includes `-p` pointing to bundled ignore file.
   - Verify the command runs against `.` (whole repo).
   - Verify non-zero return code propagates.

### Step 5: Fix lint violations in standard-tooling itself

Run the new validator against this repo's markdown. Fix any violations
surfaced by linting all `.md` files (previously only `docs/site/` +
`README.md` was checked). Delete the repo-local `.markdownlint.yaml`
and `.markdownlintignore`.

### Step 6: Validate

Run `st-docker-run -- uv run st-validate-local` to confirm all checks
pass. Iterate on violations until green.

### Step 7: Submit PR

Submit via `st-submit-pr`, wait for CI green.

## Phase 2: Release

After the PR merges:

1. Run `st-prepare-release` to cut a new patch release.
2. Follow the standard release workflow through to publish.

## Phase 3: Fleet sweep

After the release ships, sweep each repo that has a local markdownlint
config. Order from least to most markdown-heavy to surface issues
incrementally.

**Per repo:**

1. Update `standard-tooling` dependency pin in
   `standard-tooling.toml` (and `pyproject.toml` if Python).
2. Delete `.markdownlint.yaml` / `.markdownlint.json`.
3. Delete `.markdownlintignore`.
4. Delete `releases/.markdownlint.json` if present.
5. Run validation; fix any violations.
6. Submit PR via `st-submit-pr`.

**Suggested sweep order:**

1. standard-tooling-plugin (small, YAML config)
2. standard-actions (small, JSON config)
3. standards-and-conventions (YAML config)
4. standard-tooling-docker (YAML config + standalone CI job removal)
5. ai-research-methodology (YAML config with custom rules)
6. mq-rest-admin-template (JSON, minimal content)
7. mq-rest-admin-dev-environment (JSON)
8. mq-rest-admin-common (JSON + ignore)
9. mq-rest-admin-go (JSON)
10. mq-rest-admin-java (JSON)
11. mq-rest-admin-python (JSON)
12. mq-rest-admin-ruby (JSON + HTML element override)
13. mq-rest-admin-rust (JSON)

Repos with no existing config (career-strategy, laptop-upgrade,
mnemosys-core, mnemosys-operations, the-infrastructure-mindset) gain
coverage automatically when they next update their standard-tooling
pin — no dedicated sweep PR needed unless violations already exist.

## Out of scope

- Implementing Approach B (repo-local override fallback). Only added
  if a repo proves non-conformable during the sweep.
