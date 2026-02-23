# Validation Matrix

This page maps every validation check to where it runs, its trigger,
and its exit codes.

## Check Summary

| Check | Hook | CI | Script |
| ----- | ---- | -- | ------ |
| Branch naming | Yes | -- | `pre-commit` |
| Conventional Commits (single) | Yes | -- | `commit-message` |
| Repository profile | -- | Yes | `repo-profile` |
| Markdown standards | -- | Yes | `markdown-standards` |
| PR issue linkage | -- | Yes | `pr-issue-linkage` |
| Shellcheck | -- | Yes | CI workflow step |

## Local Hooks

### pre-commit

**Trigger:** Every `git commit`

| Check | Error Message | Fix |
| ----- | ------------- | --- |
| Detached HEAD | `detached HEAD is not allowed` | Create a branch |
| Protected branch | `direct commits...forbidden` | Create a feature branch |
| Bad prefix | `branch name must use...` | Rename branch |
| Missing issue | `must include a repo issue` | Rename to `type/123-desc` |

### commit-msg

**Trigger:** Every `git commit` (after pre-commit)

| Check | Error Message | Fix |
| ----- | ------------- | --- |
| Bad format | `does not follow Conventional Commits` | Use `st-commit` |

## CI Checks

### repo-profile

**Trigger:** PR opened or updated

Validates `docs/repository-standards.md` has all six required
attributes.

### markdown-standards

**Trigger:** PR opened or updated

Runs markdownlint on all markdown files. Structural checks (single
H1, TOC, heading hierarchy) apply to standard docs only -- not
doc-site pages or CHANGELOG.md.

### pr-issue-linkage

**Trigger:** PR opened or updated

Validates the PR body contains `Fixes #N`, `Closes #N`,
`Resolves #N`, or `Ref #N`.

## Exit Code Reference

| Code | Meaning | Scripts |
| ---- | ------- | ------- |
| 0 | Success | All scripts |
| 1 | Validation failure | All scripts |
| 2 | Usage error | Most lint scripts (missing args or file) |
