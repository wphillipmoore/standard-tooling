# Standard Tooling Repository Standards

## Table of Contents

- [AI co-authors](#ai-co-authors)
- [Repository profile](#repository-profile)
- [Validation policy](#validation-policy)
- [External tooling dependencies](#external-tooling-dependencies)
- [CI gates](#ci-gates)
- [Local deviations](#local-deviations)

## AI co-authors

- Co-Authored-By: wphillipmoore-codex <255923655+wphillipmoore-codex@users.noreply.github.com>
- Co-Authored-By: wphillipmoore-claude <255925739+wphillipmoore-claude@users.noreply.github.com>

## Repository profile

- repository_type: tooling
- versioning_scheme: semver
- branching_model: library-release
- release_model: tagged-release
- supported_release_lines: 1
- primary_language: shell

## Validation policy

- canonical_local_validation_command: scripts/lint/markdown-standards.sh
- validation_required: yes (markdownlint required)

## External tooling dependencies

- markdownlint (markdownlint-cli)
- shellcheck

## CI gates

Hard gates (required status checks on `develop`):

- Standards compliance (`.github/workflows/ci.yml`):
  - Repository profile validation (`scripts/lint/repo-profile.sh`)
  - Markdownlint (`scripts/lint/markdown-standards.sh`)
  - Commit message lint (`scripts/lint/commit-messages.sh`)
  - Issue linkage validation (`scripts/lint/pr-issue-linkage.sh`)
  - Shellcheck on all `.sh` scripts

Local hard gates (pre-commit hooks):

- Branch naming enforcement (`scripts/git-hooks/pre-commit`):
  branching-model-aware prefix validation.
- Commit message lint (`scripts/git-hooks/commit-msg`): Conventional Commits
  required, co-author trailer validation enforced.

## Commit and PR scripts

AI agents **must** use the wrapper scripts for commits and PR submission.
Do not construct commit messages or PR bodies manually.

### Committing

```bash
scripts/dev/commit.sh \
  --type TYPE --message MESSAGE --agent AGENT \
  [--scope SCOPE] [--body BODY]
```

- `--type` (required): `feat|fix|docs|style|refactor|test|chore|ci|build`
- `--message` (required): commit description
- `--agent` (required): `claude` or `codex`
- `--scope` (optional): conventional commit scope
- `--body` (optional): detailed commit body

The script resolves the correct `Co-Authored-By` identity from the
[AI co-authors](#ai-co-authors) section and the git hooks validate the result.

### Submitting PRs

```bash
scripts/dev/submit-pr.sh \
  --issue NUMBER --summary TEXT \
  [--linkage KEYWORD] [--title TEXT] \
  [--notes TEXT] [--docs-only] [--dry-run]
```

- `--issue` (required): GitHub issue number (just the number)
- `--summary` (required): one-line PR summary
- `--linkage` (optional, default: `Fixes`): `Fixes|Closes|Resolves|Ref`
- `--title` (optional): PR title (default: most recent commit subject)
- `--notes` (optional): additional notes
- `--docs-only` (optional): applies docs-only testing exception
- `--dry-run` (optional): print generated PR without executing

The script detects the target branch and merge strategy automatically.

## Local deviations

- None.
