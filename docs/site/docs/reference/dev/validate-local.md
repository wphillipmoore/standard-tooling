# st-validate-local

**Installed as:** `st-validate-local` (Python console script)

**Source:** `src/standard_tooling/validate_local.py`

Shared driver for pre-PR local validation. Orchestrates common checks
and language-specific validation based on the repository profile.

## Usage

```bash
st-validate-local
```

Run from the repository root. No arguments required.

## Behavior

The tool reads `primary_language` from
`docs/repository-standards.md` and runs up to three validation
stages:

### 1. Common Checks (always)

Runs `validate-local-common` (resolved via PATH). This script
contains checks shared across all repositories (markdown linting,
shellcheck, repo-profile validation).

### 2. Language-Specific Checks

If `primary_language` is set and not `none`, runs the corresponding
validation script (resolved via PATH):

| Language | Script |
| -------- | ------ |
| `python` | `validate-local-python` |
| `go` | `validate-local-go` |
| `java` | `validate-local-java` |

### 3. Custom Checks

Runs `validate-local-custom` if present on PATH or at
`scripts/bin/validate-local-custom` in the repository. This is a
repo-specific escape hatch for validation that does not fit the
common or language-specific scripts.

!!! note
    `validate-local-custom` is **not** part of standard-tooling.
    Consuming repos create and maintain it in their own
    `scripts/bin/` directory.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | All validation stages passed |
| Non-zero | One or more stages failed |
