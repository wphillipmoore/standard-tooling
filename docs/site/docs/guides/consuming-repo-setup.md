# Consuming Repo Setup

This guide walks through end-to-end onboarding of a new repository to
use standard-tooling managed scripts.

## Prerequisites

Install the required tools:

**macOS:**

```bash
brew install shellcheck
npm install --global markdownlint-cli
```

**Linux:**

```bash
sudo apt-get install shellcheck
npm install --global markdownlint-cli
```

## Step 1: Clone Standard-Tooling

Clone the canonical source alongside your repository:

```bash
git clone \
  https://github.com/wphillipmoore/standard-tooling.git
```

## Step 2: Create the Repository Profile

Create `docs/repository-standards.md` in your repository. This file
is read by multiple scripts for configuration.

Required sections:

```markdown
# Repository Standards

## Table of Contents

- [AI co-authors](#ai-co-authors)
- [Repository profile](#repository-profile)

## AI co-authors

- Co-Authored-By: your-codex <email>
- Co-Authored-By: your-claude <email>

## Repository profile

- repository_type: library
- versioning_scheme: semver
- branching_model: library-release
- release_model: tagged-release
- supported_release_lines: 1
- primary_language: python
```

## Step 3: Sync Managed Files

Run the sync script to copy all managed files:

```bash
path/to/standard-tooling/scripts/dev/sync-tooling.sh \
  --fix --ref v1.1.5
```

This creates:

- `scripts/git-hooks/pre-commit` and `commit-msg`
- `scripts/lint/*.sh` (6 lint scripts)
- `scripts/dev/*.sh` and `*.py` (10 dev scripts)

## Step 4: Configure Git Hooks

```bash
git config core.hooksPath scripts/git-hooks
```

!!! tip
    Add this to your project's setup documentation so all
    contributors configure hooks.

## Step 5: Add CI Workflow

Create `.github/workflows/ci.yml` with the standard checks:

- `scripts/lint/repo-profile.sh`
- `scripts/lint/markdown-standards.sh`
- `scripts/lint/commit-messages.sh` with base and head refs
- `scripts/lint/pr-issue-linkage.sh`
- `sync-tooling.sh --check`

See `standard-actions` for reusable workflow actions.

## Step 6: Create Markdownlint Config

Create `.markdownlint.yaml` at the repository root:

```yaml
default: true
no-duplicate-heading:
  siblings_only: true
```

## Step 7: Verify

```bash
# Verify repo profile
scripts/lint/repo-profile.sh

# Verify markdown
scripts/lint/markdown-standards.sh

# Verify hooks work
git checkout -b feature/1-test-setup
echo "test" >> test.txt
git add test.txt
scripts/dev/commit.sh \
  --type chore --message "test setup" --agent claude
```

## Keeping Up to Date

When standard-tooling releases a new version:

```bash
# See what changed
scripts/dev/sync-tooling.sh --check

# Update to new version
scripts/dev/sync-tooling.sh --fix --ref v1.2.0
```

See the [Releasing](releasing.md) guide for the full workflow.
