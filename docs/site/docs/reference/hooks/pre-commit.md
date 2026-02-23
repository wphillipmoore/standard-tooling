# pre-commit

**Path:** `scripts/lib/git-hooks/pre-commit`

Enforces branch naming conventions before allowing a commit. Reads the
`branching_model` attribute from `docs/repository-standards.md` to
determine allowed branch prefixes.

## Checks

The hook runs five checks in order:

### 1. Detached HEAD

Commits on a detached HEAD are blocked unconditionally.

### 2. Protected Branch

Direct commits to `develop`, `release`, and `main` are forbidden.

### 3. Branching Model Detection

Reads `branching_model` from `docs/repository-standards.md`. If not
found, falls back to `feature/*` and `bugfix/*` with a warning.

### 4. Branch Prefix Validation

Allowed prefixes depend on the branching model:

| Branching Model | Allowed Prefixes |
| --------------- | ---------------- |
| `docs-single-branch` | `feature/*`, `bugfix/*`, `chore/*` |
| `application-promotion` | `feature`, `bugfix`, `hotfix`, `chore`, `promo` |
| `library-release` | `feature`, `bugfix`, `hotfix`, `chore`, `release` |

### 5. Issue Number Naming

Work branches (`feature/*`, `bugfix/*`, `hotfix/*`, `chore/*`) must
include a repository issue number:

```text
{type}/{issue}-{description}
```

**Example:** `feature/42-add-caching`

`release/*` and `promotion/*` branches are exempt from this check
because they are created by automated workflows.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | All checks passed |
| 1 | Validation failure |

## Configuration

The hook reads `branching_model` from
`docs/repository-standards.md`. No other configuration is required.
