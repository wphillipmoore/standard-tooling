# commit-messages.sh

**Path:** `scripts/lint/commit-messages.sh`

Validates all commits in a range against the Conventional Commits
specification. This is the CI variant of `commit-message.sh` -- it
checks every commit between a base ref and head ref rather than a
single commit message file.

## Usage

```bash
scripts/lint/commit-messages.sh <base-ref> <head-ref>
```

**Example:**

```bash
scripts/lint/commit-messages.sh develop HEAD
```

## Behavior

1. Resolves bare branch names to `origin/` when the local branch
   does not exist.
2. Iterates over non-merge commits in the range
   `base-ref..head-ref`.
3. Validates each commit subject against the Conventional Commits
   pattern.
4. Stops at the first failing commit and reports the error.

## Cutoff SHA

Repositories that adopted Conventional Commits after initial
development can set the `COMMIT_CUTOFF_SHA` environment variable.
Commits at or before the cutoff are excluded from validation.

```bash
COMMIT_CUTOFF_SHA=abc123 \
  scripts/lint/commit-messages.sh main HEAD
```

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | All commits in range are valid |
| 1 | One or more commits failed validation |
| 2 | Missing base or head ref arguments |
