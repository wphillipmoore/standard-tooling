# Standardize markdownlint configuration across the fleet

Ref: https://github.com/wphillipmoore/standard-tooling/issues/476

## Problem

Each repo maintains its own markdownlint config with varying formats
(`.yaml` vs `.json`), rule sets, ignore patterns, and lint scopes.
Identical content passes in one repo and fails in another. Fleet-wide
changes require per-repo lint debugging.

Root cause of the triggering incident (standard-tooling-docker PR #122):
that repo runs `markdownlint .` as a standalone CI job against the
entire repo, while all other repos scope to `docs/site/**/*.md` +
`README.md` via `st-validate-local-common`.

## Decision

**Approach A: validator-owns-everything.**

The `st-validate-local-common` validator bundles the canonical config
as package data. It runs `markdownlint .` against the whole repo using
only the bundled config. Repos delete their local markdownlint configs
entirely.

If a repo genuinely cannot conform, we fall back to Approach B
(repo-local override) for that repo only, with documented justification.

## Canonical Config

Bundled at `src/standard_tooling/configs/markdownlint.yaml`:

```yaml
default: true
no-duplicate-heading:
  siblings_only: true
MD013:
  line_length: 100
  tables: false
  code_blocks: false
MD060: false
```

Bundled at `src/standard_tooling/configs/markdownlintignore`:

```
# Empty — lint everything. Add entries here only with documented justification.
```

### Rule Rationale

- `default: true` — enforce all rules unless explicitly disabled.
- `no-duplicate-heading: siblings_only` — changelogs and multi-section
  docs legitimately reuse heading text across sections.
- `MD013: line_length: 100` — matches the project's ruff line-length
  setting for consistency. Tables and code blocks are exempt because
  they commonly exceed prose width.
- `MD060: false` — enforcing visual table column alignment adds
  maintenance burden with no reader benefit.

## Validator Changes

File: `src/standard_tooling/bin/validate_local_common_container.py`

1. **Scope**: Replace `_find_markdown_files()` (which scopes to
   `docs/site/**/*.md` + `README.md`) with `markdownlint .` — lint
   the entire repo.
2. **Config resolution**: Use `importlib.resources` to resolve the
   bundled config and ignore file paths.
3. **No repo-local fallback**: Always use bundled config. Ignore any
   repo-local `.markdownlint.yaml` or `.markdownlintignore`.
4. **Remove `st-markdown-standards`**: The standalone
   `markdown_standards.py` entry point is redundant — remove the
   console script and module. This is an internal tool (not consumed
   by other repos), so no deprecation cycle is needed.
5. **Other validators unchanged**: shellcheck and yamllint invocations
   in the same file remain as-is. Only the markdownlint section
   changes.

Invocation:

```python
from importlib.resources import files

config = files("standard_tooling.configs") / "markdownlint.yaml"
ignore = files("standard_tooling.configs") / "markdownlintignore"
cmd = ["markdownlint", "--config", str(config), "-p", str(ignore), "."]
```

## Fleet Cleanup

Order of operations:

1. Ship the validator change in a standard-tooling release.
2. Sweep the fleet — each repo updates its `standard-tooling` pin,
   deletes local markdownlint configs, and fixes any violations
   surfaced by the new config.
3. Remove the standalone `markdownlint .` CI job from
   `standard-tooling-docker`'s `ci.yml`.

Per-repo cleanup:
- Delete `.markdownlint.yaml` / `.markdownlint.json`
- Delete `.markdownlintignore`
- Fix lint violations (use `markdownlint --fix .` where possible,
  manual fixes for the rest)

## Fallback Path (Approach B)

Not implemented unless forced. If a repo proves it cannot conform:

1. The validator gains a check: if a repo-local `.markdownlint.yaml`
   exists, use it instead of the bundled config. Same for
   `.markdownlintignore`.
2. The repo-local config must include a comment explaining why the
   override is necessary.
3. This escape hatch is documented but not shipped until needed.

## Affected Repos

All 19 repos with `standard-tooling.toml`:

| Repo | Current config | Action |
|------|---------------|--------|
| standard-tooling | .markdownlint.yaml | Delete |
| standard-tooling-docker | .markdownlint.yaml + standalone CI job | Delete config, remove CI job |
| standard-tooling-plugin | .markdownlint.yaml | Delete |
| standard-actions | .markdownlint.json | Delete |
| standards-and-conventions | .markdownlint.yaml | Delete |
| ai-research-methodology | .markdownlint.yaml | Delete |
| mq-rest-admin-common | .markdownlint.json | Delete |
| mq-rest-admin-dev-environment | .markdownlint.json | Delete |
| mq-rest-admin-go | .markdownlint.json | Delete |
| mq-rest-admin-java | .markdownlint.json | Delete |
| mq-rest-admin-python | .markdownlint.json | Delete |
| mq-rest-admin-ruby | .markdownlint.json | Delete |
| mq-rest-admin-rust | .markdownlint.json | Delete |
| mq-rest-admin-template | .markdownlint.json | Delete |
| career-strategy | (none) | No action |
| laptop-upgrade | (none) | No action |
| mnemosys-core | (none) | No action |
| mnemosys-operations | (none) | No action |
| the-infrastructure-mindset | (none) | No action |
