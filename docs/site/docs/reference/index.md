# Script Reference

Standard-tooling manages 18 files across three categories. All files
carry the header
`Managed by standard-tooling -- DO NOT EDIT in downstream repos`.

## Git Hooks

| Script | Purpose |
| ------ | ------- |
| [pre-commit](hooks/pre-commit.md) | Branch naming enforcement |
| [commit-msg](hooks/commit-msg.md) | Commit message validation dispatcher |

## Lint Scripts

| Script | Purpose |
| ------ | ------- |
| [commit-message.sh](lint/commit-message.md) | Single commit Conventional Commits validation |
| [co-author.sh](lint/co-author.md) | Co-author trailer validation |
| [commit-messages.sh](lint/commit-messages.md) | CI range-based commit validation |
| [repo-profile.sh](lint/repo-profile.md) | Repository profile attribute validation |
| [markdown-standards.sh](lint/markdown-standards.md) | Markdown linting and structural checks |
| [pr-issue-linkage.sh](lint/pr-issue-linkage.md) | PR body issue linkage validation |

## Dev Scripts

| Script | Purpose |
| ------ | ------- |
| [commit.sh](dev/commit.md) | Standards-compliant commit wrapper |
| [submit-pr.sh](dev/submit-pr.md) | Standards-compliant PR submission wrapper |
| [sync-tooling.sh](dev/sync-tooling.md) | Sync managed files from canonical source |
| [prepare_release.py](dev/prepare-release.md) | Automated release preparation |
| [finalize_repo.sh](dev/finalize-repo.md) | Post-merge repository cleanup |
| [validate_local.sh](dev/validate-local.md) | Local validation driver |

## Managed File List

The complete list of files synced by `sync-tooling.sh`:

```text
scripts/git-hooks/commit-msg
scripts/git-hooks/pre-commit
scripts/lint/co-author.sh
scripts/lint/commit-message.sh
scripts/lint/commit-messages.sh
scripts/lint/markdown-standards.sh
scripts/lint/pr-issue-linkage.sh
scripts/lint/repo-profile.sh
scripts/dev/commit.sh
scripts/dev/submit-pr.sh
scripts/dev/prepare_release.py
scripts/dev/finalize_repo.sh
scripts/dev/sync-tooling.sh
scripts/dev/validate_local.sh
scripts/dev/validate_local_common.sh
scripts/dev/validate_local_python.sh
scripts/dev/validate_local_go.sh
scripts/dev/validate_local_java.sh
```
