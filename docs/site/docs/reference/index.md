# Script Reference

Standard-tooling provides two categories of tools: Python CLI tools
installed as `st-*` console scripts, and bash validators consumed via
PATH.

## Python CLI Tools

| Tool | Purpose |
| ---- | ------- |
| [st-commit](dev/commit.md) | Standards-compliant commit wrapper |
| [st-submit-pr](dev/submit-pr.md) | Standards-compliant PR submission wrapper |
| [st-prepare-release](dev/prepare-release.md) | Automated release preparation |
| [st-finalize-repo](dev/finalize-repo.md) | Post-merge repository cleanup |
| [st-validate-local](dev/validate-local.md) | Local validation driver |

## Bash Validators

| Script | Purpose |
| ------ | ------- |
| [commit-message](lint/commit-message.md) | Single commit Conventional Commits validation |
| [repo-profile](lint/repo-profile.md) | Repository profile attribute validation |
| [markdown-standards](lint/markdown-standards.md) | Markdown linting and structural checks |
| [pr-issue-linkage](lint/pr-issue-linkage.md) | PR body issue linkage validation |

## Git Hooks

| Hook | Purpose |
| ---- | ------- |
| [pre-commit](hooks/pre-commit.md) | Branch naming enforcement |
| [commit-msg](hooks/commit-msg.md) | Commit message validation |

## Validation Drivers

The following bash scripts orchestrate language-specific local validation
and are consumed via PATH:

| Script | Purpose |
| ------ | ------- |
| `validate-local-common` | Shared checks (shellcheck, markdownlint) |
| `validate-local-python` | Python-specific validation |
| `validate-local-go` | Go-specific validation |
| `validate-local-java` | Java-specific validation |

These are called by `st-validate-local` based on the `primary_language`
in the repository profile.
