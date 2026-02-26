# st-submit-pr

**Installed as:** `st-submit-pr` (Python console script)

**Source:** `src/standard_tooling/submit_pr.py`

Wrapper that creates standards-compliant pull requests with
proper issue linkage, testing sections, and auto-merge configuration.

!!! warning "Required for AI agents"
    AI agents **must** use this tool instead of raw
    `gh pr create`. The tool populates the PR template and
    configures auto-merge automatically.

## Usage

```bash
st-submit-pr \
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
| `--dry-run` | No | Print PR body without executing |

### Linkage Keywords

`Fixes`, `Closes`, `Resolves`, `Ref`

## Examples

```bash
# Standard PR
st-submit-pr \
  --issue 42 --summary "Add new lint check for X"

# PR with Ref linkage
st-submit-pr \
  --issue 42 --linkage Ref \
  --summary "Update docs"

# Dry run to preview
st-submit-pr \
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
4. Pushes the branch to origin.
6. Creates the PR via `gh pr create`.
7. Enables auto-merge with the detected strategy.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | PR created and auto-merge enabled |
| 1 | Validation failure |
