# commit-msg

**Path:** `scripts/git-hooks/commit-msg`

Dispatches commit message validation to the lint scripts. This hook
runs automatically on every commit when git hooks are configured.

## Behavior

The hook calls two scripts in sequence, passing the commit message
file path:

1. **`scripts/lint/commit-message.sh`** -- validates Conventional
   Commits format
2. **`scripts/lint/co-author.sh`** -- validates Co-Authored-By
   trailers

If either script fails, the commit is rejected.

## Setup

Configure git to use the standard hooks directory:

```bash
git config core.hooksPath scripts/git-hooks
```

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Commit message is valid |
| 1 | Validation failure (from either lint script) |
