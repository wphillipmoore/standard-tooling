# Getting Started

This guide covers setting up a consuming repository to use standard-tooling
scripts.

## Prerequisites

- Git
- Bash (macOS or Linux)
- [markdownlint-cli](https://github.com/igorshubovych/markdownlint-cli):
  `npm install --global markdownlint-cli`
- [shellcheck](https://www.shellcheck.net/): `brew install shellcheck`

## Initial Setup

### 1. Clone standard-tooling

```bash
git clone https://github.com/wphillipmoore/standard-tooling.git
```

### 2. Sync scripts into your repository

From your consuming repository root:

```bash
path/to/standard-tooling/scripts/dev/sync-tooling.sh --fix --ref v1.1.5
```

This copies all managed files into your repository at the expected paths.

### 3. Configure git hooks

```bash
git config core.hooksPath scripts/git-hooks
```

This tells git to use the standard-tooling hooks for branch naming and commit
message validation.

### 4. Create a repository profile

Create `docs/repository-standards.md` with the required attributes:

```markdown
# Repository Standards

## Table of Contents

- [Repository profile](#repository-profile)

## Repository profile

- repository_type: <application|library|tooling|documentation>
- versioning_scheme: <semver|calver|none>
- branching_model: <library-release|application-promotion|docs-single-branch>
- release_model: <tagged-release|continuous-deploy|none>
- supported_release_lines: <number>
- primary_language: <python|go|java|shell|none>
```

### 5. Verify

Run the markdown linter to confirm everything is wired up:

```bash
scripts/lint/markdown-standards.sh
```

## Next Steps

- Read the [Consuming Repo Setup](guides/consuming-repo-setup.md) guide for
  detailed onboarding instructions
- See the [Script Reference](reference/index.md) for documentation on each
  managed script
- Review the [Validation Matrix](guides/validation-matrix.md) to understand
  which checks run where
