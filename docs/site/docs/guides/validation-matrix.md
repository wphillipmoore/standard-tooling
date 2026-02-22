# Validation Matrix

This page maps every validation check to where it runs, its trigger,
and its exit codes.

## Check Summary

| Check | Hook | CI | Script |
| ----- | ---- | -- | ------ |
| Branch naming | Yes | -- | `pre-commit` |
| Conventional Commits (single) | Yes | -- | `commit-message.sh` |
| Co-author trailers | Yes | -- | `co-author.sh` |
| Conventional Commits (range) | -- | Yes | `commit-messages.sh` |
| Repository profile | -- | Yes | `repo-profile.sh` |
| Markdown standards | -- | Yes | `markdown-standards.sh` |
| PR issue linkage | -- | Yes | `pr-issue-linkage.sh` |
| Shellcheck | -- | Yes | CI workflow step |
| Sync-tooling staleness | -- | Yes | `sync-tooling.sh --check` |

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
| Bad format | `does not follow Conventional Commits` | Use `commit.sh` |
| Bad co-author | `unapproved co-author trailer` | Add to repo profile |

## CI Checks

### commit-messages.sh

**Trigger:** PR opened or updated

Validates all non-merge commits in the PR range. Supports
`COMMIT_CUTOFF_SHA` for legacy repositories.

### repo-profile.sh

**Trigger:** PR opened or updated

Validates `docs/repository-standards.md` has all six required
attributes.

### markdown-standards.sh

**Trigger:** PR opened or updated

Runs markdownlint on all markdown files. Structural checks (single
H1, TOC, heading hierarchy) apply to standard docs only -- not
doc-site pages or CHANGELOG.md.

### pr-issue-linkage.sh

**Trigger:** PR opened or updated

Validates the PR body contains `Fixes #N`, `Closes #N`,
`Resolves #N`, or `Ref #N`.

### sync-tooling.sh --check

**Trigger:** PR opened or updated

Compares all 18 managed files against the latest tagged release.
Fails if any file is stale or missing.

!!! note
    Standard-tooling itself uses `skip-sync-check: "true"` because
    it is the canonical source.

## Exit Code Reference

| Code | Meaning | Scripts |
| ---- | ------- | ------- |
| 0 | Success | All scripts |
| 1 | Validation failure | All scripts |
| 2 | Usage error | Most lint scripts (missing args or file) |
