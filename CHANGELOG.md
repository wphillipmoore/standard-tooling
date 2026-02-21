# Changelog

## [develop-v1.1.2] - 2026-02-21

### ⚙️ Miscellaneous Tasks

- Merge main into release/1.1.2

## [1.1.1] - 2026-02-20

### 🐛 Bug Fixes

- Fix CHANGELOG.md formatting for markdownlint compliance

### ⚙️ Miscellaneous Tasks

- Merge main into release/1.1.1
- Prepare release 1.1.1

## [1.1.0] - 2026-02-20

### 🐛 Bug Fixes

- Fix CHANGELOG.md formatting for markdownlint compliance

### ⚙️ Miscellaneous Tasks

- Merge main into release/1.1.0
- Prepare release 1.1.0

## [1.0.3] - 2026-02-19

### 🚀 Features

- Add add-to-project workflow for standards project
- Add GitHub Project helper scripts for skill automation (#12)
- Add ci and build to allowed conventional commit types (#13)
- Add commit and PR submission wrapper scripts (#17)
- *(submit-pr)* Support cross-repo issue references (#23)
- *(release)* Add VERSION file detector to prepare_release.py (#27)
- *(ci)* Add category prefixes to CI job names (#31)
- *(validate)* Add validate_local.sh dispatch architecture (#34)
- *(hooks)* Validate issue-linked branch names in pre-commit hook (#44)
- *(ci)* Add publish workflow for automated tagging and version bumps (#46)

### 🐛 Bug Fixes

- *(lint)* Accept cross-repo issue references in PR linkage check (#36)

### 📚 Documentation

- Document release-before-sync requirement (#20)
- Ban MEMORY.md usage in CLAUDE.md (#32)
- Ban heredocs in shell commands (#33)

### ⚙️ Miscellaneous Tasks

- Add commit.sh and submit-pr.sh to managed files list (#18)
- Bump version to 1.1.1 (#37)
- *(ci)* Remove push trigger from CI workflow (#41)

## [0.0.0-test] - 2026-02-17

### 🚀 Features

- Add CI workflow, CLAUDE.md, and repository infrastructure (#6)

## [1.0.2] - 2026-02-17

### 🐛 Bug Fixes

- Prevent --actions-compat from leaking during self-update re-exec

## [1.0.1] - 2026-02-17

### 📚 Documentation

- Add canonical source comment to repo-profile.sh

## [1.0.0] - 2026-02-17

### 🚀 Features

- Initial scaffold with reconciled canonical scripts

### 🐛 Bug Fixes

- Handle empty docsite_files array with set -u
