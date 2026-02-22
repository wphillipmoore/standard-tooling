# Releasing

This guide covers the release workflow for standard-tooling and the
required ordering for syncing consuming repositories.

## Release Workflow

### 1. Develop Changes

All changes start as feature PRs targeting `develop`:

```bash
git checkout -b feature/42-add-new-check
# ... make changes ...
scripts/dev/commit.sh \
  --type feat --message "add new check" --agent claude
scripts/dev/submit-pr.sh \
  --issue 42 --summary "Add new check"
```

### 2. Prepare the Release

Once `develop` has all changes for the release, run:

```bash
scripts/dev/prepare_release.py --issue 50
```

This script:

- Creates a `release/{version}` branch from develop
- Merges main to incorporate prior release history
- Generates the changelog via git-cliff
- Creates a PR to main with auto-merge enabled

### 3. Tag the Release

After the release PR merges to main, create and push the tag:

```bash
git checkout main
git pull
git tag v1.2.0
git push origin v1.2.0
```

### 4. Finalize

Clean up local state:

```bash
scripts/dev/finalize_repo.sh
```

## Sync Ordering

!!! warning "Critical: tag before syncing"
    Consuming repos' CI runs `sync-tooling.sh --check` against the
    **latest tagged release**. If you sync consuming repos before
    tagging, their CI will fail because the tag still points to the
    old managed-files list.

**Required ordering:**

1. Merge changes to `develop` (feature PR)
2. Create a release PR to `main`, merge it, and **tag the new
   version**
3. **Only then** sync consuming repos

### Syncing Consuming Repos

After tagging:

```bash
cd path/to/consuming-repo
scripts/dev/sync-tooling.sh --fix
```

For repos that use `standard-actions`:

```bash
scripts/dev/sync-tooling.sh --fix --actions-compat
```

## Version Detection

`prepare_release.py` auto-detects the version from the project
ecosystem:

| Ecosystem | Source |
| --------- | ------ |
| Python | `pyproject.toml` |
| Maven | `pom.xml` |
| Go | `**/version.go` |
| Fallback | `VERSION` file |

Standard-tooling uses the `VERSION` file at the repository root.

## Documentation Deployment

The documentation site deploys automatically on pushes to `develop`
and `main` via `.github/workflows/docs.yml`. The version displayed
in the site is derived from `VERSION` using `cut -d. -f1,2`
(major.minor).
