# Consuming Repo Setup

This guide walks through end-to-end onboarding of a new repository to
use standard-tooling via PATH-based consumption.

## Prerequisites

Install the required tools:

**macOS:**

```bash
brew install shellcheck uv
npm install --global markdownlint-cli
```

**Linux:**

```bash
sudo apt-get install shellcheck
npm install --global markdownlint-cli
# Install uv: https://docs.astral.sh/uv/getting-started/installation/
```

## Step 1: Clone Standard-Tooling

Clone the canonical source as a sibling directory:

```bash
cd ..
git clone \
  https://github.com/wphillipmoore/standard-tooling.git
cd standard-tooling
uv sync
cd ../your-repo
```

## Step 2: Configure PATH and Hooks

Add standard-tooling to PATH and configure git hooks:

```bash
export PATH="../standard-tooling/.venv/bin:../standard-tooling/scripts/bin:$PATH"
git config core.hooksPath ../standard-tooling/scripts/lib/git-hooks
```

!!! tip
    Add the PATH export to your shell profile or project's setup
    documentation so it persists across sessions.

## Step 3: Create the Repository Profile

Create `docs/repository-standards.md` in your repository. This file
is read by multiple validators for configuration.

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

## Step 4: Add CI Workflow

Use the `standard-actions` composite action in your CI workflow:

```yaml
- name: Validate standards
  uses: wphillipmoore/standard-actions/actions/standards-compliance@develop
```

The action checks out standard-tooling, adds it to PATH, and runs:

- `repo-profile` -- validates the repository profile
- `markdown-standards` -- validates markdown formatting
- `pr-issue-linkage` -- validates PR issue linkage (on PRs only)

See `standard-actions` for reusable workflow actions.

## Step 5: Create Markdownlint Config

Create `.markdownlint.yaml` at the repository root:

```yaml
default: true
no-duplicate-heading:
  siblings_only: true
```

## Step 6: Verify

```bash
# Verify repo profile
repo-profile

# Verify markdown
markdown-standards

# Verify hooks work
git checkout -b feature/1-test-setup
echo "test" >> test.txt
git add test.txt
st-commit \
  --type chore --message "test setup" --agent claude
```

## Keeping Up to Date

Standard-tooling is consumed via PATH, so updates are picked up
automatically when you pull the latest version:

```bash
cd ../standard-tooling
git pull
uv sync
```

For CI, the `standard-actions` composite action pins to a
`standard-tooling-ref` (default: `develop`). To pin to a stable
release, set the input:

```yaml
- uses: wphillipmoore/standard-actions/actions/standards-compliance@develop
  with:
    standard-tooling-ref: v1.2
```

See the [Releasing](releasing.md) guide for the full release workflow.
