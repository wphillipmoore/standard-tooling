# commit-message.sh

**Path:** `scripts/lint/commit-message.sh`

Validates that a single commit message follows the
[Conventional Commits](https://www.conventionalcommits.org/)
specification.

## Usage

```bash
scripts/lint/commit-message.sh <commit-message-file>
```

This script is typically called by the `commit-msg` git hook, not
invoked directly.

## Validation Rules

The subject line must match:

```text
<type>(optional-scope): <description>
```

### Allowed Types

`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`,
`build`

### Merge Commits

Merge commits (subject starting with "Merge ") are allowed through
without Conventional Commits validation.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Valid commit message |
| 1 | Does not match Conventional Commits |
| 2 | Missing or invalid commit message file path |
