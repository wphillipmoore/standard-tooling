# submit-pr.sh

**Path:** `scripts/dev/submit-pr.sh`

Wrapper script that creates standards-compliant pull requests with
proper issue linkage, testing sections, and auto-merge configuration.

!!! warning "Required for AI agents"
    AI agents **must** use this script instead of raw
    `gh pr create`. The script populates the PR template and
    configures auto-merge automatically.

## Usage

```bash
scripts/dev/submit-pr.sh \
  --issue NUMBER --summary TEXT [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `--issue` | Yes | Issue number or cross-repo ref |
| `--summary` | Yes | One-line PR summary |
| `--linkage` | No | Linkage keyword (default: `Fixes`) |
| `--title` | No | PR title (default: last commit subject) |
| `--notes` | No | Additional notes for the PR |
| `--docs-only` | No | Apply docs-only testing exception |
| `--dry-run` | No | Print PR body without executing |

### Linkage Keywords

`Fixes`, `Closes`, `Resolves`, `Ref`

## Examples

```bash
# Standard PR
scripts/dev/submit-pr.sh \
  --issue 42 --summary "Add new lint check for X"

# Docs-only PR with Ref linkage
scripts/dev/submit-pr.sh \
  --issue 42 --linkage Ref \
  --summary "Update docs" --docs-only

# Dry run to preview
scripts/dev/submit-pr.sh \
  --issue 42 --summary "Fix regex bug" --dry-run
```

## Behavior

1. Validates arguments and issue reference format.
2. Detects target branch and merge strategy from the current
   branch:
    - `release/*` branches target `main` with merge strategy
    - All other branches target `develop` with squash strategy
3. Reads the testing section from
   `.github/pull_request_template.md`.
4. For `--docs-only`, replaces the testing section with changed
   file list.
5. Pushes the branch to origin.
6. Creates the PR via `gh pr create`.
7. Enables auto-merge with the detected strategy.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | PR created and auto-merge enabled |
| 1 | Validation failure |
