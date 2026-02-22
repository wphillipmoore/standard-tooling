# markdown-standards.sh

**Path:** `scripts/lint/markdown-standards.sh`

Validates markdown files using markdownlint and structural checks.
Applies different levels of validation depending on file location.

## Usage

```bash
scripts/lint/markdown-standards.sh
```

Run from the repository root. No arguments required.

## File Discovery

The script collects files from three sources:

### Standard Docs (markdownlint + structural checks)

Files found in `docs/` (excluding `docs/sphinx/`, `docs/site/`, and
`docs/announcements/`), plus `README.md` if it exists.

### Doc-Site Files (markdownlint only)

Files under `docs/sphinx/` and `docs/site/`. These are exempt from
structural checks because documentation site generators (MkDocs,
Sphinx) handle structure.

### CHANGELOG.md (markdownlint only)

`CHANGELOG.md` gets markdownlint but no structural checks because
changelog files have different heading conventions.

## Structural Checks

Applied only to standard docs, these checks enforce:

| Check | Rule |
| ----- | ---- |
| **Single H1** | Exactly one `#` heading per file |
| **Table of Contents** | A `## Table of Contents` section must exist |
| **Heading Hierarchy** | No skipped heading levels |

Code blocks (fenced with `` ``` `` or `~~~`) are excluded from
structural analysis.

## Configuration

Markdownlint uses `.markdownlint.yaml` at the repository root if
present. Otherwise it runs with default rules.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | All files pass |
| 1 | One or more validation failures |
| 2 | No markdown files found, or markdownlint not installed |
