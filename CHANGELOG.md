# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-02-23

### Bug fixes

- fix CHANGELOG.md formatting for markdownlint compliance
- fix CHANGELOG.md formatting for markdownlint compliance
- fix CHANGELOG.md formatting for markdownlint compliance
- fix CHANGELOG.md formatting for markdownlint compliance
- validate CHANGELOG.md with markdownlint before committing (#55)
- allow merge commits through commit-msg hook (#57)
- update add-to-project action to v1.0.2 (#64)

### Documentation

- document git hooks and validation rules (#71)
- add MkDocs documentation site (#72)
- update documentation site for PATH-based architecture (#79)

### Features

- annotate synced scripts with provenance comments (#58)
- add chore/ as allowed branch prefix in pre-commit hook (#66)
- restructure as Python package with PATH-based consumption (#73)
- add commit-messages range validator for CI (#76)

### Refactoring

- remove commit-messages range validator (#77)

### Testing

- achieve 100% line and branch coverage for all Python modules (#74)

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
