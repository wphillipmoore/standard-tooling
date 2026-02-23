# commit-msg

**Path:** `scripts/lib/git-hooks/commit-msg`

Validates commit messages on every commit when git hooks are configured.

## Behavior

The hook calls the `commit-message` validator, passing the commit message
file path. The validator is resolved via PATH -- either from the
repository's own `scripts/bin/` (for standard-tooling itself) or from the
standard-tooling sibling checkout.

If the validator fails, the commit is rejected.

## Setup

Configure git to use the standard-tooling hooks directory:

```bash
# For standard-tooling itself:
git config core.hooksPath scripts/lib/git-hooks

# For consuming repos (sibling checkout):
git config core.hooksPath ../standard-tooling/scripts/lib/git-hooks
```

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Commit message is valid |
| 1 | Validation failure |
