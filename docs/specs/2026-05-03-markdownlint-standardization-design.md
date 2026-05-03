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

**Validator-owns-config, scope unchanged.**

The `st-validate-local-common` validator bundles the canonical config
as package data and uses it for all repos. The lint scope stays at
`docs/site/**/*.md` + `README.md` — published, user-facing
documentation. Repos delete their local markdownlint configs entirely.

No repo-local config overrides are supported. The lint scope covers
only `docs/site/**/*.md` + `README.md` — content we fully own and
control. There is no scenario where a repo legitimately cannot conform
to the canonical rules for its own published documentation.

Rejected alternative: running `markdownlint .` against the entire repo.
This was explored and rejected during pushback review — it introduces
vendored-path exclusions, generator-compliance questions, and
fleet-wide violation cleanup for internal working documents (specs,
plans, design docs) with no user-facing benefit. The config
standardization delivers the real value; the scope expansion is where
the cost lives.

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

No ignore file is bundled. The scoped file discovery
(`docs/site/**/*.md` + `README.md`) avoids vendored, generated, and
internal content by construction.

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

1. **Scope unchanged**: Keep `_find_markdown_files()` — it discovers
   `docs/site/**/*.md` + `README.md`, which is the correct scope.
2. **Config resolution**: Use `importlib.resources` to resolve the
   bundled config path. Remove the repo-local `.markdownlint.yaml`
   check entirely — the bundled config is the only config.
3. **Remove `st-markdown-standards`**: The standalone
   `markdown_standards.py` entry point is redundant — remove the
   console script and module. This is an internal tool (not consumed
   by other repos), so no deprecation cycle is needed.
4. **Other validators unchanged**: shellcheck and yamllint invocations
   in the same file remain as-is. Only the markdownlint config
   resolution changes.

Invocation:

```python
from importlib.resources import files

config = files("standard_tooling.configs") / "markdownlint.yaml"
md_files = _find_markdown_files(repo_root)
cmd = ["markdownlint", "--config", str(config), *md_files]
```

## Fleet Cleanup

Since the lint scope is unchanged (`docs/site/**/*.md` + `README.md`),
the cleanup effort is modest — the new bundled config may surface
violations where per-repo configs were more permissive, but only in
published documentation that was already being linted.

The main work is hygiene: deleting stale per-repo markdownlint configs
that are no longer consulted, including directory-level overrides that
applied to content outside the lint scope.

Order of operations:

1. Ship the validator change in a standard-tooling release.
2. Sweep the fleet — each repo updates its `standard-tooling` pin,
   deletes all local markdownlint configs, and fixes any violations
   surfaced by the new canonical rules.
3. Remove the standalone `markdownlint .` CI job from
   `standard-tooling-docker`'s `ci.yml`.

Per-repo cleanup:
- Delete `.markdownlint.yaml` / `.markdownlint.json`
- Delete `.markdownlintignore`
- Delete `releases/.markdownlint.json` (stale directory-level override)
- Fix lint violations in `docs/site/` + `README.md` (use
  `markdownlint --fix` where possible, manual fixes for the rest)

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
