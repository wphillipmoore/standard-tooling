# Script Reference

Standard-tooling provides Python CLI tools installed as `st-*` console
scripts, plus git hooks -- all consumed via PATH.

## Python CLI Tools

| Tool | Purpose |
| ---- | ------- |
| [st-commit](dev/commit.md) | Standards-compliant commit wrapper |
| [st-submit-pr](dev/submit-pr.md) | Standards-compliant PR submission wrapper |
| [st-prepare-release](dev/prepare-release.md) | Automated release preparation |
| [st-finalize-repo](dev/finalize-repo.md) | Post-merge repository cleanup |
| [st-validate-local](dev/validate-local.md) | Local validation driver |
| [st-repo-profile](lint/repo-profile.md) | Repository profile attribute validation |
| [st-markdown-standards](lint/markdown-standards.md) | Markdown linting and structural checks |
| [st-pr-issue-linkage](lint/pr-issue-linkage.md) | PR body issue linkage validation |

## Git Hooks

| Hook | Purpose |
| ---- | ------- |
| [pre-commit](hooks/pre-commit.md) | Branch naming enforcement |

## Validation Drivers

The following `st-*` tools orchestrate language-specific local validation:

| Tool | Purpose |
| ---- | ------- |
| `st-validate-local-common` | Shared checks (shellcheck, markdownlint) |
| `st-validate-local-python` | Python-specific validation |
| `st-validate-local-go` | Go-specific validation |
| `st-validate-local-java` | Java-specific validation |

These are called by `st-validate-local` based on the `primary_language`
in the repository profile.
