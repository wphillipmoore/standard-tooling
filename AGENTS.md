# Standard Tooling - Agent Instructions

<!-- include: ./docs/repository-standards.md -->

## User Overrides (Optional)

Always apply this repository's `AGENTS.md` as the baseline. If
`~/AGENTS.md` exists and is readable, load it after and apply it as an
additive, user-specific overlay. The user-specific overlay may add
constraints but must not replace or weaken the repository instructions.
If it cannot be read, say so briefly and continue.

## Start Every Work Session: Create a Feature Branch

**Critical first step**: before making any changes in a new session, you
MUST:

1. Check current branch: `git branch --show-current`
2. If on an eternal branch (`develop`, `release`, `main`), create a feature
   branch immediately:

   ```bash
   git checkout -b feature/<descriptive-name>
   ```

3. If already on a short-lived branch, continue work there.

## Working Rules

- This repository holds shared tooling scripts. Changes here propagate to
  all consuming repositories via `sync-tooling.sh`.
- Test scripts with shellcheck before committing.
- Keep scripts portable across macOS and Linux.
- Do not add repo-specific logic; scripts must work in any consuming repo.

## Multi-Line Messages

When creating multi-line commit messages or pull request bodies, prefer using
temporary files instead of shell heredocs in command substitution. This avoids
shell escaping issues and preserves exact formatting.
