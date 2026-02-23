# st-commit

**Installed as:** `st-commit` (Python console script)

**Source:** `src/standard_tooling/commit.py`

Wrapper that constructs standards-compliant commit messages
with correct Conventional Commits format and Co-Authored-By trailers.

!!! warning "Required for AI agents"
    AI agents **must** use this tool instead of raw `git commit`.
    The tool resolves the correct co-author identity automatically.

## Usage

```bash
st-commit \
  --type TYPE --message MESSAGE --agent AGENT [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `--type` | Yes | Conventional commit type |
| `--message` | Yes | Commit description |
| `--agent` | Yes | AI tool identity: `claude` or `codex` |
| `--scope` | No | Conventional commit scope |
| `--body` | No | Detailed commit body |

### Allowed Types

`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`,
`build`

## Examples

```bash
# Feature with scope
st-commit \
  --type feat --scope lint \
  --message "add new check" --agent claude

# Bug fix
st-commit \
  --type fix \
  --message "correct regex pattern" --agent claude

# Documentation with body
st-commit \
  --type docs --message "update README" \
  --body "Expanded usage section" --agent claude
```

## Behavior

1. Validates all required arguments.
2. Reads `docs/repository-standards.md` to find the approved
   co-author identity matching the `--agent` value.
3. Verifies staged changes exist.
4. Constructs the commit message in a temporary file.
5. Runs `git commit --file` (which triggers the `commit-msg` hook
   for validation).

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Commit created successfully |
| 1 | Validation failure or missing identity |
