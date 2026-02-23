# pr-issue-linkage

**Path:** `scripts/bin/pr-issue-linkage`

Validates that a pull request body contains issue linkage. Runs in
CI using the GitHub event payload.

## Usage

This script is called by CI workflows, not invoked directly. It
reads the PR body from `$GITHUB_EVENT_PATH`.

## Validation Rules

The PR body must contain at least one line matching:

```text
Fixes #123
Closes #123
Resolves #123
Ref #123
```

Cross-repository references are also accepted:

```text
Fixes owner/repo#123
```

The pattern allows optional leading whitespace, list markers
(`-` or `*`), and an optional colon after the keyword.

## Environment

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `GITHUB_EVENT_PATH` | Yes | Path to the GitHub event JSON payload |

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Valid issue linkage found |
| 1 | No issue linkage or empty PR body |
| 2 | `GITHUB_EVENT_PATH` not set or file not found |
