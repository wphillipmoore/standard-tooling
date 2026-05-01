# standard-tooling.toml Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the markdown-based `repo_profile.py` config reader with a typed TOML reader, migrate all consumers, and clean up.

**Architecture:** A new `read_config()` function in `config.py` parses `standard-tooling.toml` into typed dataclasses (`ProjectConfig`, `StConfig`). Each consumer (`commit.py`, `validate_local.py`, `finalize_repo.py`) replaces its `repo_profile` calls with `config.read_config()`. The existing `st-config.toml` reader coexists unchanged — it's retired in a later phase.

**Tech Stack:** Python 3.11+ `tomllib`, dataclasses, pytest

**Spec:** `docs/specs/standard-tooling-toml.md` (issue #363)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `standard-tooling.toml` | Create | This repo's configuration |
| `src/standard_tooling/lib/config.py` | Modify | Add `ConfigError`, `ProjectConfig`, `StConfig`, `read_config()` |
| `tests/standard_tooling/test_config.py` | Modify | Add tests for the new TOML reader |
| `src/standard_tooling/bin/commit.py` | Modify | Replace `repo_profile` with `config.read_config()` |
| `tests/standard_tooling/test_commit.py` | Modify | Update `_commit_environment` helper and mocks |
| `src/standard_tooling/bin/validate_local.py` | Modify | Replace `repo_profile` with `config.read_config()` |
| `src/standard_tooling/bin/finalize_repo.py` | Modify | Replace `repo_profile` with `config.read_config()` |
| `src/standard_tooling/bin/repo_profile_cli.py` | Modify | Rewrite to validate `standard-tooling.toml` |
| `tests/standard_tooling/test_repo_profile_cli.py` | Modify | Rewrite profile validation tests; keep structural check tests |
| `src/standard_tooling/lib/repo_profile.py` | Delete | Entire file |
| `tests/standard_tooling/test_repo_profile.py` | Delete | Replaced by TOML reader tests |
| `docs/repository-standards.md` | Modify | Strip config sections |
| `CLAUDE.md` | Modify | Update references to `repository-standards.md` |

---

### Task 1: Seed `standard-tooling.toml`

**Files:**
- Create: `standard-tooling.toml`

- [ ] **Step 1: Create the file**

```toml
[project]
repository-type = "tooling"
versioning-scheme = "semver"
branching-model = "library-release"
release-model = "tagged-release"
primary-language = "python"

[project.co-authors]
claude = "Co-Authored-By: wphillipmoore-claude <255925739+wphillipmoore-claude@users.noreply.github.com>"
codex = "Co-Authored-By: wphillipmoore-codex <255923655+wphillipmoore-codex@users.noreply.github.com>"

[dependencies]
standard-tooling = "v1.4"
```

- [ ] **Step 2: Commit**

```bash
git add standard-tooling.toml
git commit -m "chore: seed standard-tooling.toml with this repo's values"
```

---

### Task 2: TOML Reader — Tests

**Files:**
- Modify: `tests/standard_tooling/test_config.py`

Add tests for the new `read_config()` function below the existing
`st_install_tag` tests. The existing `read_st_config` / `st_install_tag`
tests stay unchanged — that reader persists until Phase 4.

- [ ] **Step 1: Write failing tests**

Append to `tests/standard_tooling/test_config.py`:

```python
from standard_tooling.lib.config import ConfigError, read_config


# -- read_config (standard-tooling.toml) --------------------------------------

_VALID_TOML = """\
[project]
repository-type = "library"
versioning-scheme = "semver"
branching-model = "library-release"
release-model = "tagged-release"
primary-language = "python"

[project.co-authors]
claude = "Co-Authored-By: user-claude <111+user-claude@users.noreply.github.com>"

[dependencies]
standard-tooling = "v1.4"
"""


def test_read_config_valid(tmp_path: Path) -> None:
    (tmp_path / "standard-tooling.toml").write_text(_VALID_TOML)
    cfg = read_config(tmp_path)
    assert cfg.project.repository_type == "library"
    assert cfg.project.versioning_scheme == "semver"
    assert cfg.project.branching_model == "library-release"
    assert cfg.project.release_model == "tagged-release"
    assert cfg.project.primary_language == "python"
    assert "claude" in cfg.project.co_authors
    assert "user-claude" in cfg.project.co_authors["claude"]
    assert cfg.dependencies["standard-tooling"] == "v1.4"


def test_read_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="standard-tooling.toml"):
        read_config(tmp_path)


def test_read_config_invalid_toml(tmp_path: Path) -> None:
    (tmp_path / "standard-tooling.toml").write_text("[invalid\n")
    with pytest.raises(ConfigError, match="not valid TOML"):
        read_config(tmp_path)


def test_read_config_missing_project_field(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace('primary-language = "python"\n', "")
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="primary-language"):
        read_config(tmp_path)


def test_read_config_invalid_enum(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace('"library"', '"banana"')
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="repository-type.*banana"):
        read_config(tmp_path)


def test_read_config_malformed_co_author(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace(
        'claude = "Co-Authored-By: user-claude <111+user-claude@users.noreply.github.com>"',
        'claude = "not a valid trailer"',
    )
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="co-author.*claude"):
        read_config(tmp_path)


def test_read_config_missing_dependencies_key(tmp_path: Path) -> None:
    toml = _VALID_TOML.replace('standard-tooling = "v1.4"', 'other = "v1.0"')
    (tmp_path / "standard-tooling.toml").write_text(toml)
    with pytest.raises(ConfigError, match="standard-tooling"):
        read_config(tmp_path)


def test_read_config_no_co_authors(tmp_path: Path) -> None:
    lines = [
        ln
        for ln in _VALID_TOML.splitlines(keepends=True)
        if "co-authors" not in ln.lower() and "claude" not in ln
    ]
    (tmp_path / "standard-tooling.toml").write_text("".join(lines))
    cfg = read_config(tmp_path)
    assert cfg.project.co_authors == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_config.py -v -k read_config`
Expected: FAIL — `ConfigError` and `read_config` do not exist yet.

- [ ] **Step 3: Commit**

```bash
git add tests/standard_tooling/test_config.py
git commit -m "test: add failing tests for standard-tooling.toml reader"
```

---

### Task 3: TOML Reader — Implementation

**Files:**
- Modify: `src/standard_tooling/lib/config.py`

Add the new code **above** the existing `_CONFIG_FILE` / `read_st_config` /
`st_install_tag` block. The old reader stays — it's retired in Phase 4.

- [ ] **Step 1: Implement reader**

Add to `src/standard_tooling/lib/config.py` (after the existing imports,
before the `_CONFIG_FILE` constant):

```python
import re
from dataclasses import dataclass

CONFIG_FILE = "standard-tooling.toml"

_COAUTHOR_RE = re.compile(r"^Co-Authored-By:\s+.+\s+<.+>$")

_ENUMS: dict[str, set[str]] = {
    "repository-type": {"library", "application", "infrastructure", "tooling", "documentation"},
    "versioning-scheme": {"library", "semver", "application", "none"},
    "branching-model": {"library-release", "application-promotion", "docs-single-branch"},
    "release-model": {"artifact-publishing", "tagged-release", "environment-promotion", "none"},
    "primary-language": {"python", "go", "java", "ruby", "rust", "shell", "none"},
}

_PROJECT_FIELDS = (
    "repository-type",
    "versioning-scheme",
    "branching-model",
    "release-model",
    "primary-language",
)


class ConfigError(Exception):
    """Raised when standard-tooling.toml has invalid content."""


@dataclass
class ProjectConfig:
    repository_type: str
    versioning_scheme: str
    branching_model: str
    release_model: str
    primary_language: str
    co_authors: dict[str, str]


@dataclass
class StConfig:
    project: ProjectConfig
    dependencies: dict[str, str]


def read_config(repo_root: Path) -> StConfig:
    """Parse, validate, and return ``standard-tooling.toml``."""
    config_path = repo_root / CONFIG_FILE
    if not config_path.is_file():
        msg = f"{CONFIG_FILE} not found at {repo_root}"
        raise FileNotFoundError(msg)

    try:
        with config_path.open("rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        msg = f"{CONFIG_FILE} is not valid TOML: {exc}"
        raise ConfigError(msg) from exc

    project_raw = raw.get("project", {})

    for field in _PROJECT_FIELDS:
        if field not in project_raw or not project_raw[field]:
            msg = f"{CONFIG_FILE}: missing or empty required field '{field}'"
            raise ConfigError(msg)

    for field in _PROJECT_FIELDS:
        value = project_raw[field]
        if value not in _ENUMS[field]:
            allowed = ", ".join(sorted(_ENUMS[field]))
            msg = f"{CONFIG_FILE}: invalid {field} '{value}' (allowed: {allowed})"
            raise ConfigError(msg)

    co_authors: dict[str, str] = {}
    co_authors_raw = project_raw.get("co-authors", {})
    for name, trailer in co_authors_raw.items():
        if not _COAUTHOR_RE.match(trailer):
            msg = (
                f"{CONFIG_FILE}: malformed co-author trailer for '{name}': "
                f"{trailer!r}"
            )
            raise ConfigError(msg)
        co_authors[name] = trailer

    deps = raw.get("dependencies", {})
    if "standard-tooling" not in deps:
        msg = f"{CONFIG_FILE}: [dependencies] must contain 'standard-tooling'"
        raise ConfigError(msg)

    project = ProjectConfig(
        repository_type=project_raw["repository-type"],
        versioning_scheme=project_raw["versioning-scheme"],
        branching_model=project_raw["branching-model"],
        release_model=project_raw["release-model"],
        primary_language=project_raw["primary-language"],
        co_authors=co_authors,
    )
    return StConfig(project=project, dependencies=dict(deps))
```

Update the imports block at the top of the file — add `re` and `dataclass`:

The file's existing imports are `os`, `tomllib`, `Path` (TYPE_CHECKING),
and `Any`. Add `re` alongside `os`, and `dataclass` from `dataclasses`.
Move `Path` out of TYPE_CHECKING since `read_config` uses it at runtime.

- [ ] **Step 2: Run tests to verify they pass**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_config.py -v`
Expected: All tests PASS (both old `read_st_config` tests and new `read_config` tests).

- [ ] **Step 3: Commit**

```bash
git add src/standard_tooling/lib/config.py
git commit -m "feat: add typed TOML reader for standard-tooling.toml"
```

---

### Task 4: Migrate `commit.py`

**Files:**
- Modify: `src/standard_tooling/bin/commit.py`
- Modify: `tests/standard_tooling/test_commit.py`

Two changes: (a) refactor `_validate_commit_context()` to accept `root`
and `branching_model` as parameters instead of reading the profile
internally, (b) replace `resolve_co_author()` with a dict lookup on
`StConfig.project.co_authors`.

- [ ] **Step 1: Update test helper and mocks**

In `tests/standard_tooling/test_commit.py`:

Replace the import line:

```python
from standard_tooling.bin.commit import main, parse_args
```

with:

```python
from standard_tooling.bin.commit import _validate_commit_context, main, parse_args
```

Replace the `_commit_environment` helper (lines 18–62) with:

```python
_TEST_TOML_TEMPLATE = """\
[project]
repository-type = "library"
versioning-scheme = "semver"
branching-model = "{branching_model}"
release-model = "tagged-release"
primary-language = "python"

[project.co-authors]
claude = "Co-Authored-By: test <test@test.com>"
codex = "Co-Authored-By: test-codex <codex@test.com>"

[dependencies]
standard-tooling = "v1.4"
"""


@contextlib.contextmanager
def _commit_environment(
    tmp_path: Path,
    *,
    branch: str = "feature/42-test",
    is_main_worktree: bool = False,
    branching_model: str = "library-release",
    has_staged: bool = True,
    write_config: bool = True,
) -> Iterator[None]:
    """Set up mocks for `commit.main()`.

    Defaults represent a happy path: secondary worktree, library-release
    config, valid feature/42-test branch, staged changes present.

    When *write_config* is True (default), a ``standard-tooling.toml``
    is written with the given *branching_model*.  Set *write_config*
    to False to test the no-config fallback path.
    """
    if write_config:
        (tmp_path / "standard-tooling.toml").write_text(
            _TEST_TOML_TEMPLATE.format(branching_model=branching_model)
        )

    with (
        patch("standard_tooling.bin.commit.git.current_branch", return_value=branch),
        patch("standard_tooling.bin.commit.git.repo_root", return_value=tmp_path),
        patch(
            "standard_tooling.bin.commit.git.is_main_worktree",
            return_value=is_main_worktree,
        ),
        patch(
            "standard_tooling.bin.commit.git.has_staged_changes",
            return_value=has_staged,
        ),
        patch("standard_tooling.bin.commit.git.run"),
    ):
        yield
```

Replace `test_main_no_staged_changes` (lines 99–118) with:

```python
def test_main_no_staged_changes(tmp_path: Path) -> None:
    with _commit_environment(tmp_path, has_staged=False):
        result = main(["--type", "feat", "--message", "test", "--agent", "claude"])
    assert result == 1
```

Replace `test_main_with_staged_changes_no_scope` (lines 121–148):

```python
def test_main_with_staged_changes_no_scope(tmp_path: Path) -> None:
    commit_file_content = ""

    def capture_run(*args: str) -> None:
        nonlocal commit_file_content
        if args[0] == "commit" and args[1] == "--file":
            commit_file_content = Path(args[2]).read_text(encoding="utf-8")

    with _commit_environment(tmp_path):
        with patch("standard_tooling.bin.commit.git.run", side_effect=capture_run):
            result = main(["--type", "feat", "--message", "add feature", "--agent", "claude"])
    assert result == 0
    assert commit_file_content.startswith("feat: add feature\n")
    assert "Co-Authored-By: test <test@test.com>" in commit_file_content
```

Replace `test_main_with_scope_and_body` (lines 150–191):

```python
def test_main_with_scope_and_body(tmp_path: Path) -> None:
    commit_file_content = ""

    def capture_run(*args: str) -> None:
        nonlocal commit_file_content
        if args[0] == "commit" and args[1] == "--file":
            commit_file_content = Path(args[2]).read_text(encoding="utf-8")

    with _commit_environment(tmp_path):
        with patch("standard_tooling.bin.commit.git.run", side_effect=capture_run):
            result = main(
                [
                    "--type",
                    "fix",
                    "--scope",
                    "lint",
                    "--message",
                    "correct regex",
                    "--body",
                    "Fixed edge case",
                    "--agent",
                    "claude",
                ]
            )
    assert result == 0
    assert "fix(lint): correct regex" in commit_file_content
    assert "Fixed edge case" in commit_file_content
    assert "Co-Authored-By: test <test@test.com>" in commit_file_content
```

Replace the two fallback tests (`test_validate_falls_back_when_no_profile`
and `test_validate_fallback_rejects_hotfix`) to test
`_validate_commit_context` directly, since the no-config path now also
fails co-author resolution before it gets to the staged-changes check:

```python
def test_validate_falls_back_when_no_config(tmp_path: Path) -> None:
    with patch("standard_tooling.bin.commit.git.current_branch", return_value="feature/42-test"):
        assert _validate_commit_context(tmp_path, "") == 0


def test_validate_fallback_rejects_hotfix(tmp_path: Path) -> None:
    with patch("standard_tooling.bin.commit.git.current_branch", return_value="hotfix/42-urgent"):
        assert _validate_commit_context(tmp_path, "") == 1
```

Update `test_validate_admits_normal_branch` to provide a branching_model
(it previously relied on fallback + mocked co-author):

```python
def test_validate_admits_normal_branch(tmp_path: Path) -> None:
    with _commit_environment(tmp_path, branch="feature/42-test", branching_model="library-release"):
        assert main(_DEFAULT_ARGS) == 0
```

Replace `test_validate_rejects_unknown_branching_model` — the reader's
enum validation now catches invalid models at parse time (tested in
`test_config.py`), so test `_validate_commit_context` directly for the
runtime path:

```python
def test_validate_rejects_unknown_branching_model(tmp_path: Path) -> None:
    with patch("standard_tooling.bin.commit.git.current_branch", return_value="feature/42-thing"):
        assert _validate_commit_context(tmp_path, "bogus-model") == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_commit.py -v`
Expected: FAIL — `commit.py` still imports `repo_profile`.

- [ ] **Step 3: Update `commit.py`**

Replace the import (line 19):

```python
from standard_tooling.lib import git, repo_profile
```

with:

```python
from standard_tooling.lib import config, git
```

Replace `_validate_commit_context` signature and its config-reading
block (lines 73–119). The function now takes `root` and
`branching_model` as params. Remove lines 95–101 (profile reading)
and 104/112 (`repo_profile.PROFILE_FILENAME` references):

```python
def _validate_commit_context(root: Path, branching_model: str) -> int:
    """Run the five branch / context checks before any commit.

    Returns 0 on success, 1 on rejection (with diagnostic on stderr).
    """
    current_branch = git.current_branch()

    # Check 1: detached HEAD
    if current_branch == "HEAD":
        return _reject(
            "ERROR: detached HEAD is not allowed for commits.",
            "Create a short-lived branch and open a PR.",
        )

    # Check 2: protected branches
    if current_branch in _PROTECTED_BRANCHES:
        return _reject(
            f"ERROR: direct commits to protected branches are forbidden ({current_branch}).",
            "Create a short-lived branch and open a PR.",
        )

    if branching_model and branching_model not in _BRANCHING_MODELS:
        return _reject(
            f"ERROR: unrecognized branching_model '{branching_model}' "
            f"in {config.CONFIG_FILE}.",
        )

    if branching_model:
        allowed_regex, allowed_display = _BRANCHING_MODELS[branching_model]
    else:
        print(
            f"WARNING: branching_model not found in {config.CONFIG_FILE}; "
            "falling back to feature/*/bugfix/*.",
            file=sys.stderr,
        )
        allowed_regex = r"^(feature|bugfix|chore)/"
        allowed_display = "feature/*, bugfix/*, or chore/*"

    # Check 3: branch prefix matches branching model
    if not re.search(allowed_regex, current_branch):
        return _reject(
            f"ERROR: branch name must use {allowed_display} ({current_branch}).",
            "Rename the branch before committing.",
        )

    # Check 4: feature/bugfix/hotfix/chore branches must include an issue number
    if _ISSUE_REQUIRED_RE.search(current_branch) and not _ISSUE_FORMAT_RE.match(current_branch):
        return _reject(
            f"ERROR: branch name must include a repo issue number ({current_branch}).",
            "Expected format: {type}/{issue}-{description}",
            "Example: feature/42-add-caching",
        )

    # Check 5: feature-branch commits from the main worktree are forbidden
    # when `.worktrees/` is present (worktree-convention rule 3).
    if (
        _WORKTREE_SCOPED_RE.search(current_branch)
        and (root / _WORKTREES_DIRNAME).is_dir()
        and git.is_main_worktree()
    ):
        return _reject(
            "ERROR: feature-branch commits from the main worktree are forbidden "
            f"({current_branch}).",
            "The main worktree is read-only under the worktree convention; "
            "edits flow through a worktree on a feature branch.",
            "To proceed:",
            f"  cd {root}/{_WORKTREES_DIRNAME}/<issue-N-slug>  "
            "# if a worktree already exists for this branch",
            f"  git worktree add {_WORKTREES_DIRNAME}/issue-N-<slug> "
            f"-b {current_branch} origin/develop  # to create one",
            "See docs/specs/worktree-convention.md for the full convention.",
        )

    return 0
```

Replace `main()` (lines 159–201):

```python
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = git.repo_root()

    try:
        st_config = config.read_config(root)
        branching_model = st_config.project.branching_model
    except FileNotFoundError:
        st_config = None
        branching_model = ""
    except config.ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rc = _validate_commit_context(root, branching_model)
    if rc != 0:
        return rc

    if st_config is None or args.agent not in st_config.project.co_authors:
        print(
            f"ERROR: no co-author identity for agent '{args.agent}' "
            f"in {config.CONFIG_FILE}.",
            file=sys.stderr,
        )
        return 1
    identity = st_config.project.co_authors[args.agent]

    if not git.has_staged_changes():
        print(
            "ERROR: no staged changes. Stage files with 'git add' before committing.",
            file=sys.stderr,
        )
        return 1

    subject = args.commit_type
    if args.scope:
        subject = f"{subject}({args.scope})"
    subject = f"{subject}: {args.message}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(f"{subject}\n")
        if args.body:
            f.write(f"\n{args.body}\n")
        f.write(f"\n{identity}\n")
        tmp_path = f.name

    try:
        git.run("commit", "--file", tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return 0
```

Also add `Path` to the runtime imports (it was already imported but
may be behind `TYPE_CHECKING`). The existing `from pathlib import Path`
on line 17 is already a runtime import — no change needed.

Update the module docstring (line 1) — replace
`docs/repository-standards.md` with `standard-tooling.toml`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_commit.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/standard_tooling/bin/commit.py tests/standard_tooling/test_commit.py
git commit -m "refactor: migrate st-commit from repo_profile to config.read_config"
```

---

### Task 5: Migrate `validate_local.py`

**Files:**
- Modify: `src/standard_tooling/bin/validate_local.py`

No test changes needed — `test_validate_local.py` does not mock `repo_profile`.

- [ ] **Step 1: Update the module**

Replace line 17:

```python
from standard_tooling.lib import git, repo_profile
```

with:

```python
from standard_tooling.lib import config, git
```

Replace lines 58–62:

```python
    try:
        profile = repo_profile.read_profile(root)
        primary_language = profile.primary_language
    except FileNotFoundError:
        primary_language = ""
```

with:

```python
    try:
        st_config = config.read_config(root)
        primary_language = st_config.project.primary_language
    except FileNotFoundError:
        primary_language = ""
    except config.ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
```

Update the module docstring (line 3) — replace
`docs/repository-standards.md` with `standard-tooling.toml`.

- [ ] **Step 2: Run tests**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_validate_local.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add src/standard_tooling/bin/validate_local.py
git commit -m "refactor: migrate st-validate-local from repo_profile to config.read_config"
```

---

### Task 6: Migrate `finalize_repo.py`

**Files:**
- Modify: `src/standard_tooling/bin/finalize_repo.py`

No test changes needed — `test_finalize_repo.py` does not mock `repo_profile`.

- [ ] **Step 1: Update the module**

Replace line 20:

```python
from standard_tooling.lib import git, repo_profile
```

with:

```python
from standard_tooling.lib import config, git
```

Replace lines 157–161:

```python
    try:
        profile = repo_profile.read_profile(root)
        model = profile.branching_model
    except FileNotFoundError:
        model = ""
```

with:

```python
    try:
        st_config = config.read_config(root)
        model = st_config.project.branching_model
    except FileNotFoundError:
        model = ""
    except config.ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
```

- [ ] **Step 2: Run tests**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_finalize_repo.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add src/standard_tooling/bin/finalize_repo.py
git commit -m "refactor: migrate st-finalize-repo from repo_profile to config.read_config"
```

---

### Task 7: Rewrite `repo_profile_cli.py` — Tests

**Files:**
- Modify: `tests/standard_tooling/test_repo_profile_cli.py`

Keep the structural check tests (lines 131–197) unchanged. Replace the
profile validation tests (lines 1–128) with TOML validation tests.

- [ ] **Step 1: Rewrite the profile validation section**

Replace lines 1–128 (everything above the `# -- _structural_check` section)
with:

```python
"""Tests for standard_tooling.bin.repo_profile_cli."""

from __future__ import annotations

from typing import TYPE_CHECKING

from standard_tooling.bin.repo_profile_cli import _structural_check, main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


_VALID_TOML = """\
[project]
repository-type = "library"
versioning-scheme = "semver"
branching-model = "library-release"
release-model = "tagged-release"
primary-language = "python"

[project.co-authors]
claude = "Co-Authored-By: user-claude <111+user-claude@users.noreply.github.com>"

[dependencies]
standard-tooling = "v1.4"
"""


def _write_toml(tmp_path: Path, content: str) -> None:
    (tmp_path / "standard-tooling.toml").write_text(content)


# -- TOML validation ----------------------------------------------------------


def test_valid_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_toml(tmp_path, _VALID_TOML)
    assert main() == 0


def test_missing_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main() == 2


def test_missing_field(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    toml = _VALID_TOML.replace('primary-language = "python"\n', "")
    _write_toml(tmp_path, toml)
    assert main() == 1


def test_invalid_enum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    toml = _VALID_TOML.replace('"library"', '"banana"')
    _write_toml(tmp_path, toml)
    assert main() == 1


def test_malformed_co_author(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    toml = _VALID_TOML.replace(
        'claude = "Co-Authored-By: user-claude <111+user-claude@users.noreply.github.com>"',
        'claude = "not a trailer"',
    )
    _write_toml(tmp_path, toml)
    assert main() == 1


def test_missing_dependencies_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    toml = _VALID_TOML.replace('standard-tooling = "v1.4"', 'other = "v1.0"')
    _write_toml(tmp_path, toml)
    assert main() == 1
```

The structural check tests (lines 131+) and the `main`+README integration
tests (lines 176+) stay exactly as-is.

**Update the `main`+README integration tests** (lines 179–196): replace
the `_mock_profile_ok` calls with real TOML files:

```python
def test_main_readme_structural_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_toml(tmp_path, _VALID_TOML)
    (tmp_path / "README.md").write_text("## No H1\n")
    assert main() == 1


def test_main_readme_structural_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_toml(tmp_path, _VALID_TOML)
    (tmp_path / "README.md").write_text("# Title\n\n## Table of Contents\n\n## Section\n")
    assert main() == 0


def test_main_no_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_toml(tmp_path, _VALID_TOML)
    assert main() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_repo_profile_cli.py -v`
Expected: FAIL — `repo_profile_cli.py` still reads from markdown.

- [ ] **Step 3: Commit**

```bash
git add tests/standard_tooling/test_repo_profile_cli.py
git commit -m "test: rewrite repo-profile-cli tests for TOML validation"
```

---

### Task 8: Rewrite `repo_profile_cli.py` — Implementation

**Files:**
- Modify: `src/standard_tooling/bin/repo_profile_cli.py`

Keep `_structural_check` and the README checks. Replace the profile
validation with a call to `config.read_config()`.

- [ ] **Step 1: Rewrite the module**

Replace the entire file with:

```python
"""Validate the repository configuration and README structure.

Checks that ``standard-tooling.toml`` is valid (required fields,
enum values, co-author format, dependencies), then validates
README.md structural conventions (exactly one H1, a Table of
Contents heading, no heading-level skips).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from standard_tooling.lib.config import CONFIG_FILE, ConfigError, read_config

_CODE_FENCE_RE = re.compile(r"^(```|~~~)")
_TOC_RE = re.compile(r"^## Table of Contents\s*$")
_HEADING_RE = re.compile(r"^(#{1,6}) ")


def _structural_check(file_path: str) -> bool:
    """Validate README structural conventions. Return True if valid."""
    in_code = False
    toc_found = False
    h1_count = 0
    last_level = 0
    errors: list[str] = []

    lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    for line_num, line in enumerate(lines, start=1):
        if _CODE_FENCE_RE.match(line):
            in_code = not in_code

        if in_code:
            continue

        if _TOC_RE.match(line):
            toc_found = True

        m = _HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            if level == 1:
                h1_count += 1
            if last_level > 0 and level > last_level + 1:
                errors.append(
                    f"ERROR: Heading level skips from {last_level} to {level} "
                    f"({file_path}:{line_num})"
                )
            last_level = level

    if h1_count != 1:
        errors.append(f"ERROR: expected exactly one H1 heading, found {h1_count} ({file_path})")

    if not toc_found:
        errors.append(f"ERROR: missing ## Table of Contents ({file_path})")

    for error in errors:
        print(error, file=sys.stderr)

    return len(errors) == 0


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    try:
        read_config(Path.cwd())
    except FileNotFoundError:
        print(
            f"ERROR: {CONFIG_FILE} not found",
            file=sys.stderr,
        )
        return 2
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    readme = Path("README.md")
    if readme.is_file() and not _structural_check(str(readme)):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_repo_profile_cli.py -v`
Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
git add src/standard_tooling/bin/repo_profile_cli.py
git commit -m "refactor: rewrite repo-profile-cli to validate standard-tooling.toml"
```

---

### Task 9: Delete Old Code

**Files:**
- Delete: `src/standard_tooling/lib/repo_profile.py`
- Delete: `tests/standard_tooling/test_repo_profile.py`

- [ ] **Step 1: Verify no remaining imports**

Run:

```bash
grep -rn 'repo_profile' src/standard_tooling/ --include='*.py' | grep -v '__pycache__'
```

Expected: only `validate_local_common_container.py` (which imports
`repo_profile_cli`, not `repo_profile`) and `markdown_standards.py`
(a comment, not an import). If any other hits appear, they are
leftover references — fix them before proceeding.

- [ ] **Step 2: Delete the files**

```bash
git rm src/standard_tooling/lib/repo_profile.py
git rm tests/standard_tooling/test_repo_profile.py
```

- [ ] **Step 3: Run full validation**

Run: `st-docker-run -- uv run st-validate-local`
Expected: All checks PASS.

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: delete repo_profile.py — replaced by config.read_config"
```

---

### Task 10: Strip Config from Docs and Update References

**Files:**
- Modify: `docs/repository-standards.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Strip config sections from `docs/repository-standards.md`**

Remove these three sections entirely:
- **AI co-authors** (lines 12–15)
- **Repository profile** (lines 17–24)
- **Validation policy** (lines 26–29)

Update the Table of Contents to remove the deleted entries. The
remaining sections stay: External tooling dependencies, CI gates,
Commit and PR scripts, Local deviations.

The result should look like:

```markdown
# Standard Tooling Repository Standards

## Table of Contents

- [External tooling dependencies](#external-tooling-dependencies)
- [CI gates](#ci-gates)
- [Local deviations](#local-deviations)

## External tooling dependencies

- markdownlint (markdownlint-cli)
- shellcheck
- uv

## CI gates
...
```

- [ ] **Step 2: Update `CLAUDE.md`**

In the `CLAUDE.md` section **Architecture > Python Package**, the
`repo_profile.py` entry says "Parse `docs/repository-standards.md`".
Replace it with a description of `config.py`:

```markdown
- **`config.py`** — Parse `standard-tooling.toml` and `st-config.toml`
```

Remove the `repo_profile.py` bullet entirely.

In the **Architecture > Key Constraints** or any other section that
references `docs/repository-standards.md` as a config source, update
to reference `standard-tooling.toml`.

Update the `Commit and PR scripts` reference in docs/repository-standards.md
line 73–74: change "the [AI co-authors](#ai-co-authors) section" to
reference `standard-tooling.toml`:

```markdown
The script resolves the correct `Co-Authored-By` identity from
`standard-tooling.toml` and the git hooks validate the result.
```

- [ ] **Step 3: Run full validation**

Run: `st-docker-run -- uv run st-validate-local`
Expected: All checks PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/repository-standards.md CLAUDE.md
git commit -m "docs: strip config sections from repository-standards.md, update references"
```

---

## Post-Implementation

After all tasks are complete, run full validation one final time:

```bash
st-docker-run -- uv run st-validate-local
```

Then submit the PR with `st-submit-pr --issue 363`.
