# Getting Started

This guide covers setting up a consuming repository to use standard-tooling.

## Prerequisites

- Git
- Bash (macOS or Linux)
- [uv](https://docs.astral.sh/uv/): Python package manager
- [markdownlint-cli](https://github.com/igorshubovych/markdownlint-cli):
  `npm install --global markdownlint-cli`
- [shellcheck](https://www.shellcheck.net/): `brew install shellcheck`

## Initial Setup

### 1. Clone standard-tooling

Clone standard-tooling as a sibling directory alongside your repository:

```bash
git clone https://github.com/wphillipmoore/standard-tooling.git
```

### 2. Install the Python package

```bash
cd standard-tooling
uv sync
```

This installs the `st-*` CLI tools into `.venv/bin/`.

### 3. Add standard-tooling to PATH

From your consuming repository:

```bash
export PATH="../standard-tooling/.venv/bin:../standard-tooling/scripts/bin:$PATH"
```

This makes both the Python CLI tools (`st-commit`, `st-submit-pr`, etc.)
and bash validators (`repo-profile`, `markdown-standards`, etc.) available
by bare name.

### 4. Configure git hooks

```bash
git config core.hooksPath ../standard-tooling/scripts/lib/git-hooks
```

This tells git to use the standard-tooling hooks for branch naming and commit
message validation.

### 5. Create a repository profile

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

### 6. Verify

Run a validator to confirm everything is wired up:

```bash
repo-profile
```

## Next Steps

- Read the [Consuming Repo Setup](guides/consuming-repo-setup.md) guide for
  detailed onboarding instructions including CI configuration
- See the [Script Reference](reference/index.md) for documentation on each
  tool
- Review the [Validation Matrix](guides/validation-matrix.md) to understand
  which checks run where
