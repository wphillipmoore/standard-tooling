# co-author.sh

**Path:** `scripts/lint/co-author.sh`

Validates `Co-Authored-By` trailers in commit messages against the
approved identities listed in `docs/repository-standards.md`.

## Usage

```bash
scripts/lint/co-author.sh <commit-message-file>
```

This script is typically called by the `commit-msg` git hook, not
invoked directly.

## Validation Rules

1. **No trailers** -- human-only commits (no `Co-Authored-By` lines)
   are always valid.
2. **Approved identities** -- each `Co-Authored-By` trailer must
   match an entry in the `AI co-authors` section of
   `docs/repository-standards.md`.
3. **Whitespace normalization** -- comparison normalizes whitespace
   so minor formatting differences do not cause false failures.

## Repository Profile Format

The approved identities are listed as bullet items:

```markdown
## AI co-authors

- Co-Authored-By: name <email>
- Co-Authored-By: name <email>
```

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | All trailers approved (or no trailers present) |
| 1 | One or more unapproved trailers found |
| 2 | Missing or invalid commit message file path |
