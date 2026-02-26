# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.1] - 2026-02-26

### Bug fixes

- resolve commit-msg hook fallback relative to hook directory, not consuming repo (#90)
- disable fail-fast in docker-publish matrix (#100)
- bump Go dev images from 1.23 to 1.25 and 1.26 (#105)
- use v2 module path for go-licenses (#107)
- use hadolint binary instead of container to avoid musl/node24 incompatibility (#122)
- suppress DL3028 hadolint warning for gem version pinning (#123)
- exclude auto-generated markdown from markdownlint (#125)
- add SHELL pipefail directive to all Dockerfiles (#127)
- expand trivyignore with upstream-unfixable CVEs (#128)

### CI

- migrate CI to three-tier model (#112)

### Documentation

- add three-tier CI architecture guide (#109)

### Features

- add Ruby ecosystem detection to st-prepare-release (#88)
- add st-observatory CLI for cross-repo health reports (#91)
- allow dots in branch name validation (#93)
- add Docker dev images and docker-test script (#96)
- publish dev container images to GHCR (#98)
- add shellcheck and markdownlint to all dev images (#110)
- generate per-release verbose release notes files (#114)
- add CI quality gates for dev container images (#121)
- harden dev images with patched base packages, Node 22 LTS, shellcheck 0.11.0 (#126)

### Refactoring

- remove --docs-only flag from st-submit-pr (#117)

## [1.2.0] - 2026-02-23

### Bug fixes

- update add-to-project action to v1.0.2 (#64)
- read version from pyproject.toml in publish and docs workflows (#82)

### Documentation

- document git hooks and validation rules (#71)
- add MkDocs documentation site (#72)
- update documentation site for PATH-based architecture (#79)

### Features

- add chore/ as allowed branch prefix in pre-commit hook (#66)
- restructure as Python package with PATH-based consumption (#73)
- add commit-messages range validator for CI (#76)

### Refactoring

- remove commit-messages range validator (#77)

### Testing

- achieve 100% line and branch coverage for all Python modules (#74)

## [1.1.4] - 2026-02-21

### Bug fixes

- fix CHANGELOG.md formatting for markdownlint compliance
- fix CHANGELOG.md formatting for markdownlint compliance
- fix CHANGELOG.md formatting for markdownlint compliance
- fix CHANGELOG.md formatting for markdownlint compliance
- validate CHANGELOG.md with markdownlint before committing (#55)
- allow merge commits through commit-msg hook (#57)

### Features

- annotate synced scripts with provenance comments (#58)

## [1.1.3] - 2026-02-21

### Bug fixes

- strip ^{} suffix from dereferenced tags in sync-tooling.sh (#51)

## [1.1.2] - 2026-02-21

### Bug fixes

- handle empty docsite_files array with set -u
- prevent --actions-compat from leaking during self-update re-exec
- accept cross-repo issue references in PR linkage check (#36)

### Documentation

- add canonical source comment to repo-profile.sh
- document release-before-sync requirement (#20)
- ban MEMORY.md usage in CLAUDE.md (#32)
- ban heredocs in shell commands (#33)

### Features

- initial scaffold with reconciled canonical scripts
- add CI workflow, CLAUDE.md, and repository infrastructure (#6)
- add add-to-project workflow for standards project
- add GitHub Project helper scripts for skill automation (#12)
- add ci and build to allowed conventional commit types (#13)
- add commit and PR submission wrapper scripts (#17)
- support cross-repo issue references (#23)
- add VERSION file detector to prepare_release.py (#27)
- add category prefixes to CI job names (#31)
- add validate_local.sh dispatch architecture (#34)
- validate issue-linked branch names in pre-commit hook (#44)
- add publish workflow for automated tagging and version bumps (#46)
