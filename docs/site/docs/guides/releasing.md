# Releasing

This guide covers the release workflow for standard-tooling.

## Release Workflow

### 1. Develop Changes

All changes start as feature PRs targeting `develop`:

```bash
git checkout -b feature/42-add-new-check
# ... make changes ...
st-commit \
  --type feat --message "add new check" --agent claude
st-submit-pr \
  --issue 42 --summary "Add new check"
```

### 2. Prepare the Release

Once `develop` has all changes for the release, run:

```bash
st-prepare-release --issue 50
```

This tool:

- Creates a `release/{version}` branch from develop
- Merges main to incorporate prior release history
- Generates the changelog via git-cliff
- Creates a PR to main with auto-merge enabled

### 3. Post-Merge Automation

After the release PR merges to main, CI automation handles:

- Creating and pushing the `v{version}` tag
- Creating the GitHub Release
- Publishing the package artifact
- Deploying documentation
- Creating an automated version bump PR to develop

### 4. Finalize

Clean up local state:

```bash
st-finalize-repo
```

## Consuming Repo Updates

Standard-tooling is consumed via PATH, so consuming repos pick up
updates automatically when their sibling checkout is updated:

```bash
cd ../standard-tooling
git pull
uv sync
```

For CI, consuming repos use `standard-actions` which pins to a
`standard-tooling-ref`. After tagging a new release, update the
default ref in the `standards-compliance` action.

## Version Detection

`st-prepare-release` auto-detects the version from the project
ecosystem:

| Ecosystem | Source |
| --------- | ------ |
| Python | `pyproject.toml` |
| Maven | `pom.xml` |
| Go | `**/version.go` |
| Fallback | `VERSION` file |

## Documentation Deployment

The documentation site deploys automatically on pushes to `develop`
and `main` via `.github/workflows/docs.yml`. The version displayed
in the site is derived from the project version using major.minor.
