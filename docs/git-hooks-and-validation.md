# Git Hooks and Validation

## Table of Contents

- [Overview](#overview)
- [Git Hooks](#git-hooks)
  - [Enabling Hooks](#enabling-hooks)
  - [pre-commit](#pre-commit)
  - [commit-msg](#commit-msg)
- [Lint Scripts](#lint-scripts)
  - [commit-message.sh](#commit-messagesh)
  - [co-author.sh](#co-authorsh)
  - [commit-messages.sh](#commit-messagessh)
  - [repo-profile.sh](#repo-profilesh)
  - [markdown-standards.sh](#markdown-standardssh)
  - [pr-issue-linkage.sh](#pr-issue-linkagesh)
- [Validation Matrix](#validation-matrix)
- [Configuration Points](#configuration-points)
- [Exit Code Conventions](#exit-code-conventions)
- [Error Reference](#error-reference)

## Overview

This repository enforces code quality through two complementary
entry points that share a common set of lint scripts:

- **Git hooks** run locally on every commit, providing
  immediate feedback before code reaches the remote.
- **CI workflows** run the same lint scripts on pull requests,
  ensuring standards are enforced even when hooks are not
  installed.

All hooks and lint scripts are managed by standard-tooling.
Consuming repositories receive them via `sync-tooling.sh` and
must not modify them directly.

## Git Hooks

### Enabling Hooks

Point Git at the managed hooks directory:

```bash
git config core.hooksPath scripts/git-hooks
```

This must be run once per clone. It is not persisted across
fresh clones.

### pre-commit

The pre-commit hook runs five checks in order. Any failure
blocks the commit.

**1. Detached HEAD check** — Commits on a detached HEAD are
blocked unconditionally. Create a named branch first.

**2. Protected branch check** — Direct commits to `develop`,
`release`, and `main` are forbidden. These branches accept
changes only through pull requests.

**3. Branching model lookup** — The hook reads
`branching_model` from `docs/repository-standards.md` to
determine which branch prefixes are allowed.

**4. Branch prefix check** — The current branch name must
match one of the allowed prefixes for the repository's
branching model:

- **docs-single-branch** — `feature/*`, `bugfix/*`, `chore/*`
- **application-promotion** — `feature/*`, `bugfix/*`,
  `hotfix/*`, `chore/*`, `promotion/*`
- **library-release** — `feature/*`, `bugfix/*`, `hotfix/*`,
  `chore/*`, `release/*`

If the branching model is missing, the hook falls back to
`feature/*`, `bugfix/*`, and `chore/*` with a warning.

**5. Issue number check** — Work branches (`feature/*`,
`bugfix/*`, `hotfix/*`, `chore/*`) must include a repository
issue number in the branch name. The required format is:

```text
{type}/{issue}-{description}
```

For example: `feature/42-add-caching`. The `release/*` and
`promotion/*` prefixes are exempt because they are created by
automated workflows and have no associated issue.

The full pattern:
`^(feature|bugfix|hotfix|chore)/[0-9]+-[a-z0-9][a-z0-9-]*$`

### commit-msg

The commit-msg hook dispatches to two lint scripts in order:

1. `scripts/lint/commit-message.sh` — validates Conventional
   Commits format
2. `scripts/lint/co-author.sh` — validates Co-Authored-By
   trailers

Both must pass for the commit to proceed.

## Lint Scripts

### commit-message.sh

Validates that the commit subject line follows Conventional
Commits format.

**Input**: path to the commit message file (single commit).

**Pattern**:
`^(feat|fix|docs|style|refactor|test|chore|ci|build)(\([^\)]+\))?: .+`

**Allowed types**: `feat`, `fix`, `docs`, `style`, `refactor`,
`test`, `chore`, `ci`, `build`.

Merge commits (subject starting with `Merge`) bypass
validation entirely.

### co-author.sh

Validates that any `Co-Authored-By` trailers in the commit
message match an approved identity listed in the repository
profile.

**Input**: path to the commit message file.

**Behavior**:

- If the commit has no `Co-Authored-By` trailers, it passes
  (human-only commits are always valid).
- If trailers are present, each one must match an entry from
  `docs/repository-standards.md` under lines matching
  `^- Co-Authored-By:`.
- Whitespace is normalized before comparison.

### commit-messages.sh

CI variant of commit message validation. Checks all non-merge
commits in a range rather than a single commit.

**Usage**: `commit-messages.sh <base-ref> <head-ref>`

**COMMIT_CUTOFF_SHA**: Environment variable that excludes
legacy commits predating the Conventional Commits convention.
Commits at or before this SHA are skipped during validation.

Bare branch names are resolved to `origin/` automatically
when the local branch does not exist.

### repo-profile.sh

Validates that `docs/repository-standards.md` contains all
six required attributes with non-placeholder values.

**Required attributes**:

- `repository_type`
- `versioning_scheme`
- `branching_model`
- `release_model`
- `supported_release_lines`
- `primary_language`

Values containing `<`, `>`, or `|` are rejected as
placeholders.

### markdown-standards.sh

Validates markdown files using markdownlint and structural
checks.

**File discovery**:

- Standard docs: all `*.md` files under `docs/`, excluding
  `docs/sphinx/`, `docs/site/`, and `docs/announcements/`.
  Also includes `README.md` if present.
- Doc-site files: `*.md` under `docs/sphinx/` and
  `docs/site/` (markdownlint only, no structural checks).
- `CHANGELOG.md`: markdownlint only (no structural checks).

**Structural checks** (standard docs only):

- Exactly one H1 heading per file
- A `## Table of Contents` section must be present
- No heading level skips (e.g., jumping from H2 to H4)

Code blocks (fenced with `` ``` `` or `~~~`) are excluded
from structural analysis.

### pr-issue-linkage.sh

CI-only script that validates pull request bodies contain
issue linkage.

**Requires**: `GITHUB_EVENT_PATH` environment variable
pointing to the GitHub Actions event payload JSON.

**Accepted linkage keywords**: `Fixes`, `Closes`,
`Resolves`, `Ref` — followed by `#123` or a cross-repo
reference like `owner/repo#123`.

The keyword may optionally include a colon and may appear
as a list item.

## Validation Matrix

The following table shows where each validation runs:

- **pre-commit**: runs locally before each commit
- **commit-msg**: runs locally on the commit message
- **CI**: runs in GitHub Actions on pull requests

| Validation             | pre-commit | commit-msg | CI |
|------------------------|:----------:|:----------:|:--:|
| Detached HEAD          | yes        |            |    |
| Protected branch       | yes        |            |    |
| Branch prefix          | yes        |            |    |
| Issue number in branch | yes        |            |    |
| Conventional Commits   |            | yes        | yes|
| Co-author trailers     |            | yes        |    |
| Commit messages range  |            |            | yes|
| Repository profile     |            |            | yes|
| Markdown standards     |            |            | yes|
| PR issue linkage       |            |            | yes|

## Configuration Points

**`docs/repository-standards.md`** — The repository profile
is the primary configuration surface. It controls:

- **`branching_model`**: Determines which branch prefixes
  the pre-commit hook allows.
- **`Co-Authored-By` entries**: Defines approved AI agent
  identities for the co-author trailer check.
- **Six required attributes**: Validated by
  `repo-profile.sh` in CI.

**`.markdownlint.yaml`** — Controls markdownlint rules.
When present, `markdown-standards.sh` passes it via
`--config`.

**`COMMIT_CUTOFF_SHA`** — Environment variable used by
`commit-messages.sh` to exclude legacy commits from
Conventional Commits validation.

## Exit Code Conventions

All hooks and lint scripts follow a consistent exit code
scheme:

- **`0`** — Validation passed.
- **`1`** — Validation failed. The input does not meet
  the required standard.
- **`2`** — Usage error. Required input is missing or the
  environment is misconfigured (e.g., missing file path
  argument, `markdownlint` not installed,
  `GITHUB_EVENT_PATH` not set).

## Error Reference

**`"ERROR: detached HEAD is not allowed for commits."`**
— The pre-commit hook blocks commits on a detached HEAD.
Create a named branch before committing.

**`"ERROR: direct commits to protected branches are
forbidden"`** — The pre-commit hook blocks commits to
`develop`, `release`, or `main`. Create a feature branch
and open a pull request.

**`"ERROR: branch name must use {prefixes}"`** — The
current branch does not match any allowed prefix for the
repository's branching model. Rename the branch.

**`"WARNING: branching_model not found"`** — The
repository profile does not contain a `branching_model`
attribute. The hook falls back to `feature/*`, `bugfix/*`,
and `chore/*`. Add the attribute to suppress this warning.

**`"ERROR: branch name must include a repo issue number"`**
— Work branches must follow the `{type}/{issue}-{desc}`
format. Example: `feature/42-add-caching`.

**`"ERROR: unrecognized branching_model"`** — The
`branching_model` value in the repository profile is not
one of the three supported models.

**`"ERROR: commit message does not follow Conventional
Commits."`** — The commit subject line does not match the
required pattern. Use the format
`<type>(optional-scope): <description>`.

**`"ERROR: unapproved co-author trailer"`** — A
`Co-Authored-By` trailer does not match any approved
identity in `docs/repository-standards.md`.

**`"ERROR: no approved co-author identities found"`** —
The repository profile exists but contains no
`Co-Authored-By` entries. Add approved identities.

**`"ERROR: repository profile missing required attribute"`**
— One of the six required attributes is not present in
`docs/repository-standards.md`.

**`"ERROR: repository profile attribute appears to be a
placeholder"`** — An attribute value contains `<`, `>`,
or `|`, indicating it has not been filled in.

**`"ERROR: no markdown files found to lint."`** — No
markdown files were discovered. Ensure docs exist under
`docs/` or that `README.md` is present.

**`"ERROR: markdownlint not found."`** — The
`markdownlint` CLI is not installed. Run
`npm install --global markdownlint-cli`.

**`"ERROR: pull request body is empty"`** — The PR has
no body text. Add issue linkage to the PR description.

**`"ERROR: pull request body must include primary issue
linkage"`** — The PR body does not contain a recognized
linkage keyword (`Fixes`, `Closes`, `Resolves`, or `Ref`)
followed by an issue reference.

**`"ERROR: commit message file path is required."`** —
The lint script was called without a file argument. This
typically indicates a misconfigured hook.

**`"ERROR: repository profile not found"`** — The file
`docs/repository-standards.md` does not exist. Create it
with the required attributes.

**`"ERROR: base and head refs are required."`** —
`commit-messages.sh` was called without both ref
arguments. Usage: `commit-messages.sh <base> <head>`.
