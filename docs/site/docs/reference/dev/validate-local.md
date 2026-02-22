# validate_local.sh

**Path:** `scripts/dev/validate_local.sh`

Shared driver for pre-PR local validation. Orchestrates common checks
and language-specific validation based on the repository profile.

## Usage

```bash
scripts/dev/validate_local.sh
```

Run from the repository root. No arguments required.

## Behavior

The script reads `primary_language` from
`docs/repository-standards.md` and runs up to three validation
stages:

### 1. Common Checks (always)

Runs `scripts/dev/validate_local_common.sh` if present. This script
contains checks shared across all repositories (markdown linting,
shellcheck, etc.).

### 2. Language-Specific Checks

If `primary_language` is set and not `none`, runs the corresponding
script:

| Language | Script |
| -------- | ------ |
| `python` | `validate_local_python.sh` |
| `go` | `validate_local_go.sh` |
| `java` | `validate_local_java.sh` |

### 3. Custom Checks

Runs `scripts/dev/validate_local_custom.sh` if present. This is a
repo-specific escape hatch for validation that does not fit the
common or language-specific scripts.

!!! note
    `validate_local_custom.sh` is **not** a managed file. Consuming
    repos can create and maintain it freely.

## Language Validation Scripts

The language-specific scripts are managed files synced by
`sync-tooling.sh`:

- `validate_local_common.sh`
- `validate_local_python.sh`
- `validate_local_go.sh`
- `validate_local_java.sh`

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | All validation stages passed |
| Non-zero | One or more stages failed |
