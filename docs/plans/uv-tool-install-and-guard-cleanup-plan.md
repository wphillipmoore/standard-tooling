# uv tool install and guard cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `pip install` with `uv tool install` in the Docker cache build, remove `shutil.which` guard patterns, make silent fallbacks fatal, and eliminate all `pip install` references from documentation.

**Architecture:** Five targeted file changes in `src/standard_tooling/` plus a spec update. Each file has its guards/fallbacks removed independently. The `docker_cache.py` change is the core fix (PEP 668); the other files are guard-pattern cleanup driven by the same "just run the command" principle. A final audit task catches any remaining catch-and-suppress patterns.

**Tech Stack:** Python 3.14, pytest, unittest.mock

**Spec:** `docs/specs/2026-04-30-uv-tool-install-and-guard-cleanup-design.md`

---

### Task 1: `docker_cache.py` — replace pip with uv and make failures fatal

**Files:**
- Modify: `src/standard_tooling/lib/docker_cache.py:87-153`
- Test: `tests/standard_tooling/test_docker_cache.py`

- [ ] **Step 1: Update test for uv command string**

In `tests/standard_tooling/test_docker_cache.py`, the `test_build_cached_image_success` test (line 266) verifies the build works but doesn't assert the install command string. Add a test that verifies `uv tool install` is in the docker create command:

```python
def test_build_cached_image_uses_uv_tool_install(tmp_path: Path) -> None:
    (tmp_path / "standard-tooling.toml").write_text(_VALID_TOML)
    create_result = MagicMock(returncode=0, stdout="abc123\n")
    ok = MagicMock(returncode=0)
    create_cmd: list[str] = []

    def mock_run(cmd, **_kwargs):  # noqa: ANN001, ANN003
        if cmd[1] == "create":
            create_cmd.extend(cmd)
            return create_result
        return ok

    with patch("standard_tooling.lib.docker_cache.subprocess.run", side_effect=mock_run):
        _build_cached_image(tmp_path, "go", "img:1", "img:1--branch--hash")
    setup_cmd = create_cmd[-1]
    assert "uv tool install" in setup_cmd
    assert "pip install" not in setup_cmd
```

- [ ] **Step 2: Run test to verify it fails**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_docker_cache.py::test_build_cached_image_uses_uv_tool_install -v`
Expected: FAIL — the current code still uses `pip install`.

- [ ] **Step 3: Update tests for fatal failures**

Replace `test_build_cached_image_create_fails` and `test_build_cached_image_start_fails` to expect exceptions instead of base image fallback:

```python
def test_build_cached_image_create_fails(tmp_path: Path) -> None:
    (tmp_path / "standard-tooling.toml").write_text(_VALID_TOML)
    create_result = MagicMock(returncode=1, stderr="no space")
    with (
        patch("standard_tooling.lib.docker_cache.subprocess.run", return_value=create_result),
        pytest.raises(RuntimeError, match="Failed to create container"),
    ):
        _build_cached_image(tmp_path, "go", "img:1", "img:1--branch--hash")


def test_build_cached_image_start_fails(tmp_path: Path) -> None:
    (tmp_path / "standard-tooling.toml").write_text(_VALID_TOML)
    create_result = MagicMock(returncode=0, stdout="abc123\n")
    start_result = MagicMock(returncode=1)
    rm_result = MagicMock(returncode=0)

    def mock_run(cmd, **_kwargs):  # noqa: ANN001, ANN003
        if cmd[1] == "create":
            return create_result
        if cmd[1] == "start":
            return start_result
        return rm_result

    with (
        patch("standard_tooling.lib.docker_cache.subprocess.run", side_effect=mock_run),
        pytest.raises(RuntimeError, match="Cache build failed"),
    ):
        _build_cached_image(tmp_path, "go", "img:1", "img:1--branch--hash")
```

Add `pytest` to the imports at the top of the test file (it's not currently imported directly — add `import pytest` after the existing imports).

- [ ] **Step 4: Run failure tests to verify they fail**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_docker_cache.py::test_build_cached_image_create_fails tests/standard_tooling/test_docker_cache.py::test_build_cached_image_start_fails -v`
Expected: FAIL — the current code returns base image instead of raising.

- [ ] **Step 5: Implement the changes in `docker_cache.py`**

In `src/standard_tooling/lib/docker_cache.py`, make three changes:

**5a.** Replace the pip install command (line 95):

```python
# Before
pip_install = f"pip install --quiet 'standard-tooling @ git+{_ST_GIT_URL}@{tag}'"
warmup = _WARMUP_COMMANDS.get(lang)
setup = f"{pip_install} && {warmup}" if warmup else pip_install

# After
uv_install = f"uv tool install --quiet 'standard-tooling @ git+{_ST_GIT_URL}@{tag}'"
warmup = _WARMUP_COMMANDS.get(lang)
setup = f"{uv_install} && {warmup}" if warmup else uv_install
```

**5b.** Make container creation failure fatal (lines 121-126):

```python
# Before
if cid_result.returncode != 0:
    print(
        f"ERROR: Failed to create container: {cid_result.stderr.strip()}",
        file=sys.stderr,
    )
    return base_image

# After
if cid_result.returncode != 0:
    msg = f"Failed to create container: {cid_result.stderr.strip()}"
    raise RuntimeError(msg)
```

**5c.** Make cache build failure fatal (lines 134-139):

```python
# Before
if run_result.returncode != 0:
    print(
        "ERROR: Cache build failed. Falling back to base image.",
        file=sys.stderr,
    )
    return base_image

# After
if run_result.returncode != 0:
    msg = "Cache build failed"
    raise RuntimeError(msg)
```

**5d.** Update the print output (line 101) to say `Install` instead of referencing pip:

```python
print(f"  Install: standard-tooling@{tag}")
```

This line already says `Install:` without mentioning pip, so no change needed — verify it's correct and move on.

- [ ] **Step 6: Run all docker_cache tests**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_docker_cache.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```
git add src/standard_tooling/lib/docker_cache.py tests/standard_tooling/test_docker_cache.py
git commit -m "fix: replace pip install with uv tool install in docker cache build

Make _build_cached_image raise RuntimeError on container creation
failure and cache build failure instead of silently returning the
base image.

Ref #427, Ref #429"
```

---

### Task 2: `finalize_repo.py` — remove fallback chain, gh guard, and make docs failure fatal

**Files:**
- Modify: `src/standard_tooling/bin/finalize_repo.py`
- Test: `tests/standard_tooling/test_finalize_repo.py`

- [ ] **Step 1: Update tests — remove shutil.which patches and fallback test**

In `tests/standard_tooling/test_finalize_repo.py`:

**1a.** Delete the `_which_docker_only` and `_which_validator_only` helper functions (lines 82-89). They simulate the old fallback logic.

**1b.** Delete `test_main_falls_back_to_direct_validator` (lines 276-289). This tests the fallback path being removed.

**1c.** Delete `test_main_validator_not_found` (lines 229-239). The new behavior raises `FileNotFoundError` instead of returning 1.

**1d.** Update `test_main_prefers_docker_run` — rename to `test_main_calls_docker_run` and remove the `shutil.which` patch. Instead, patch `subprocess.run` to capture the command:

```python
def test_main_calls_docker_run(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()) as mock_sub,
        patch(_MOD + "._check_docs_workflow_status", return_value=None),
    ):
        result = main([])
    assert result == 0
    cmd = mock_sub.call_args[0][0]
    assert cmd[0] == "st-docker-run"
    assert cmd[1:] == ("--", "st-validate-local")
```

**1e.** Update `test_main_docker_run_uses_uv_for_python` — remove the `shutil.which` patch:

```python
def test_main_docker_run_uses_uv_for_python(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()) as mock_sub,
        patch(_MOD + "._check_docs_workflow_status", return_value=None),
    ):
        result = main([])
    assert result == 0
    cmd = mock_sub.call_args[0][0]
    assert cmd == ("st-docker-run", "--", "uv", "run", "st-validate-local")
```

**1f.** Update all remaining `main()` tests that patch `shutil.which` — remove those patches and add `patch(_MOD + "._check_docs_workflow_status", return_value=None)` instead. The affected tests are:
- `test_main_library_release`
- `test_main_already_on_target`
- `test_main_no_profile`
- `test_main_application_promotion`
- `test_main_docs_single_branch`
- `test_main_no_deleted_branches`
- `test_main_validation_fails`
- `test_main_removes_worktree_before_deleting_branch`
- `test_main_skips_worktree_remove_when_branch_not_in_worktree`
- `test_main_cleans_docker_cache_on_branch_delete`

For each, remove the `patch(_MOD + ".shutil.which", ...)` line and add `patch(_MOD + "._check_docs_workflow_status", return_value=None)`.

**1g.** Verify no `shutil.which` patches remain in any test file that patches a module being cleaned up:

Run: `grep -rn "shutil.which" tests/ --include='*.py'`
Expected: Only `test_validate_local.py` (out of scope — legitimate discovery) and `test_pre_commit_gate.py` (direct call to locate bash, not a mock).

- [ ] **Step 2: Update test — docs workflow failure is now fatal**

Replace `test_main_warns_on_docs_failure_but_returns_zero` (lines 400-424) with a test that asserts exit code 1:

```python
def test_main_returns_one_on_docs_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()),
        patch(
            _MOD + "._check_docs_workflow_status",
            return_value=(
                "Documentation workflow run 999 on develop (deadbee) "
                "ended with conclusion 'failure'."
            ),
        ),
    ):
        result = main([])
    assert result == 1
    stderr = capsys.readouterr().err
    assert "Documentation workflow" in stderr
```

- [ ] **Step 3: Update tests — remove shutil.which patches from `_check_docs_workflow_status` tests**

All `_check_docs_workflow_status` tests currently patch `shutil.which`. Remove those patches. The tests that mock `subprocess.run` directly will continue to work — `subprocess.run` is what gets called now.

Delete `test_check_docs_workflow_returns_none_when_gh_missing` (lines 310-312) entirely — this tested the removed guard.

For the remaining `_check_docs_workflow_status` tests, remove the `patch(_MOD + ".shutil.which", return_value="/usr/bin/gh")` line from each:
- `test_check_docs_workflow_returns_none_when_gh_fails`
- `test_check_docs_workflow_returns_none_when_no_runs`
- `test_check_docs_workflow_returns_none_on_success`
- `test_check_docs_workflow_returns_none_on_in_progress`
- `test_check_docs_workflow_returns_message_on_failure`
- `test_check_docs_workflow_returns_none_on_malformed_json`
- `test_check_docs_workflow_returns_none_on_empty_stdout`

- [ ] **Step 4: Run tests to verify they fail**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_finalize_repo.py -v`
Expected: FAIL — implementation still uses old patterns.

- [ ] **Step 5: Implement the changes in `finalize_repo.py`**

**5a.** Remove the `shutil` import (line 16):

```python
# Delete this line:
import shutil
```

**5b.** Remove the `shutil.which("gh")` guard in `_check_docs_workflow_status` (lines 97-99). Change the function to call `gh` directly via subprocess. Replace:

```python
gh = shutil.which("gh")
if gh is None:
    return None
result = subprocess.run(  # noqa: S603
    [
        gh,
        "run",
```

with:

```python
result = subprocess.run(  # noqa: S603
    [
        "gh",  # noqa: S607
        "run",
```

**5c.** Replace the post-finalization validation block (lines 225-255). Remove the `shutil.which` checks and fallback chain. Replace the entire block with:

```python
    validation_failed = False
    if not args.dry_run:
        print()
        print("Running post-finalization validation via st-docker-run...")
        repo_root = Path(git.repo_root())
        if (repo_root / "pyproject.toml").is_file():
            cmd: tuple[str, ...] = ("st-docker-run", "--", "uv", "run", "st-validate-local")
        else:
            cmd = ("st-docker-run", "--", "st-validate-local")

        result = subprocess.run(cmd, check=False)  # noqa: S603, S607
        if result.returncode != 0:
            validation_failed = True
    else:
        print("  [dry-run] st-docker-run -- [uv run] st-validate-local")
```

**5d.** Make docs workflow failure fatal. Replace the soft-warning block at the end of `main()` (around lines 277-290):

```python
# Before (soft warning, exit 0):
    if docs_failure is not None:
        print()
        print(
            "WARNING: most recent Documentation workflow run did not succeed.",
            file=sys.stderr,
        )
        print(f"  {docs_failure}", file=sys.stderr)
        print(
            "  Docs publish is async — investigate before the next merge so",
            file=sys.stderr,
        )
        print("  the site doesn't drift further from develop.", file=sys.stderr)
        # Soft warning: keep exit code 0 since finalize itself succeeded.

# After (fatal):
    if docs_failure is not None:
        print()
        print(
            "ERROR: most recent Documentation workflow run did not succeed.",
            file=sys.stderr,
        )
        print(f"  {docs_failure}", file=sys.stderr)
        return 1
```

- [ ] **Step 6: Run all finalize_repo tests**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_finalize_repo.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```
git add src/standard_tooling/bin/finalize_repo.py tests/standard_tooling/test_finalize_repo.py
git commit -m "refactor: remove guard patterns and fallback chain from finalize_repo

Remove shutil.which guards for st-docker-run, st-validate-local,
and gh. Always call st-docker-run for validation. Make docs
workflow failure fatal (exit 1 instead of soft warning).

Ref #427"
```

---

### Task 3: `prepare_release.py` — remove `_ensure_tool`

**Files:**
- Modify: `src/standard_tooling/bin/prepare_release.py`
- Test: `tests/standard_tooling/test_prepare_release.py`

- [ ] **Step 1: Update tests — remove `_ensure_tool` tests and imports**

In `tests/standard_tooling/test_prepare_release.py`:

**1a.** Remove `_ensure_tool` from the import list (line 24).

**1b.** Delete `test_ensure_tool_found` and `test_ensure_tool_not_found` (lines 302-312).

**1c.** In `test_main_full_flow`, `test_main_release_branch_already_exists`, `test_main_no_publishable_changes`, and `test_main_full_flow_with_release_notes` — remove the `patch("standard_tooling.bin.prepare_release.shutil.which", ...)` line from each.

- [ ] **Step 2: Run tests to verify they fail**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_prepare_release.py -v`
Expected: FAIL — `_ensure_tool` import will fail once removed from source, and `shutil.which` patches will be patching a removed import.

- [ ] **Step 3: Implement the changes in `prepare_release.py`**

**3a.** Remove the `shutil` import (line 25):

```python
# Delete this line:
import shutil
```

**3b.** Delete the `_ensure_tool` function (lines 167-169):

```python
# Delete these lines:
def _ensure_tool(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"Required tool '{name}' not found on PATH.")
```

**3c.** Remove the `_ensure_tool("git-cliff")` call in `_generate_changelog` (line 200):

```python
# Delete this line:
_ensure_tool("git-cliff")
```

**3d.** Remove the `_ensure_tool("gh")` call in `main()` (line 293):

```python
# Delete this line:
_ensure_tool("gh")
```

- [ ] **Step 4: Run all prepare_release tests**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_prepare_release.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```
git add src/standard_tooling/bin/prepare_release.py tests/standard_tooling/test_prepare_release.py
git commit -m "refactor: remove _ensure_tool guard from prepare_release

Both gh and git-cliff are called immediately via subprocess; if
either is missing, FileNotFoundError surfaces the problem clearly.
The pre-check added no diagnostic value.

Ref #427"
```

---

### Task 4: `markdown_standards.py` — remove markdownlint guard

**Files:**
- Modify: `src/standard_tooling/bin/markdown_standards.py`
- Test: `tests/standard_tooling/test_markdown_standards.py`

- [ ] **Step 1: Update tests — remove shutil.which patches and guard test**

In `tests/standard_tooling/test_markdown_standards.py`:

**1a.** Delete `test_main_markdownlint_missing` (lines 50-54). This tested the removed guard.

**1b.** In `test_main_pass`, `test_main_fail`, and `test_main_with_config` — remove the `patch("standard_tooling.bin.markdown_standards.shutil.which", ...)` line from each. The `subprocess.run` mock will handle the command call.

- [ ] **Step 2: Run tests to verify they fail**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_markdown_standards.py -v`
Expected: FAIL — `shutil.which` patches will be patching a removed import.

- [ ] **Step 3: Implement the changes in `markdown_standards.py`**

**3a.** Remove the `shutil` import (line 3):

```python
# Delete this line:
import shutil
```

**3b.** Remove the markdownlint guard (lines 34-36):

```python
# Delete these lines:
    if not shutil.which("markdownlint"):
        print("FATAL: markdownlint not found on PATH", file=sys.stderr)
        return 2
```

- [ ] **Step 4: Run all markdown_standards tests**

Run: `st-docker-run -- uv run pytest tests/standard_tooling/test_markdown_standards.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```
git add src/standard_tooling/bin/markdown_standards.py tests/standard_tooling/test_markdown_standards.py
git commit -m "refactor: remove markdownlint guard from markdown_standards

markdownlint runs inside the dev container where it must be
present. If missing, subprocess.run raises FileNotFoundError with
a clear traceback.

Ref #427"
```

---

### Task 5: `host-level-tool.md` — eliminate all pip install references

**Files:**
- Modify: `docs/specs/host-level-tool.md`

- [ ] **Step 1: Identify all pip install references**

Run: `grep -n "pip install\|pip_install\|pip .*install" docs/specs/host-level-tool.md`

The known locations from the spec:
1. Deployment targets table — "Developer host" row mentions `pip install` as alternative
2. Deployment targets table — "Non-Python container runtime" row says `pip install`
3. Lines 144-174: `uv tool install` vs `pip install` comparison table and surrounding prose
4. Cache-first runtime install section — "pre-installed via `pip install`"
5. Upgrade section — `pip install` upgrade command and "For `pip install` users" block
6. standard-tooling-docker migration steps — `pip install` instruction

- [ ] **Step 2: Remove all pip install references**

**2a.** In the deployment targets table (line 94 area):
- "Developer host" row: change install mechanism to just `uv tool install from git URL` (remove the `pip install from git URL (alternative)` part)
- "Non-Python container runtime" row: change `pip install` to `uv tool install`

**2b.** Delete the entire `### uv tool install vs pip install` section (lines 144-174 area), including the comparison table and all surrounding prose about `pip install` being an "alternative."

**2c.** In the "Upgrade (host)" section: delete the `For pip install users:` block and the `pip install --upgrade` command. Keep only the `uv tool upgrade` command.

**2d.** In the "Cache-first runtime install" section: change "pre-installed via `pip install` from the git URL" to "pre-installed via `uv tool install` from the git URL."

**2e.** In the "standard-tooling-docker migration steps" section: change `pip install 'standard-tooling @ git+…@v1.2'` to `uv tool install 'standard-tooling @ git+…@v1.2'`.

**2f.** Search for any remaining references and update them.

- [ ] **Step 3: Verify no pip install references remain**

Run: `grep -rn "pip install" docs/specs/host-level-tool.md`
Expected: No output.

Run: `grep -rn "pip install" docs/ CLAUDE.md`
Expected: No standard-tooling references (may have references in other contexts like general Python docs — those are fine).

- [ ] **Step 4: Commit**

```
git add docs/specs/host-level-tool.md
git commit -m "docs: remove all pip install references from host-level-tool spec

uv tool install is the only documented install mechanism for
standard-tooling. Remove the pip install alternative, comparison
table, and upgrade instructions.

Ref #429"
```

---

### Task 6: Warning-to-fatal audit

**Files:**
- Read: all files under `src/standard_tooling/`
- Possibly modify: files where catch-and-suppress patterns are found

- [ ] **Step 1: Audit all except clauses**

Run: `grep -rn 'except.*:\|except:' src/standard_tooling/ --include='*.py'`

Review each hit against principle 6: "Errors are fatal by default." For each exception handler, determine whether it:
- **(A) Propagates the error** (re-raises, returns error code, raises different exception) — OK, leave it.
- **(B) Suppresses the error** (returns None, returns 0, silently continues, logs a warning and continues) — needs justification or conversion to fatal.

Known exception handlers to audit (from the grep in context exploration):

| File | Line | Pattern | Expected verdict |
|---|---|---|---|
| `check_pr_merge.py:89,103,164` | `except ValueError` | Parsing PR numbers from strings | Legitimate — input validation |
| `check_pr_merge.py:173` | `except CalledProcessError` | gh CLI failure | Review — may need to propagate |
| `validate_local.py:61` | `except FileNotFoundError` | Missing config file | Legitimate — optional config |
| `validate_local.py:63` | `except ConfigError` | Bad config | Legitimate — prints error, returns 1 |
| `repo_profile_cli.py:68,74` | `except FileNotFoundError/ConfigError` | Config handling | Legitimate — prints error |
| `docker_test.py:63` | `except (FileNotFoundError, TimeoutExpired)` | Docker version check | Review — same pattern as `assert_docker_available` |
| `finalize_repo.py:74` | `except ValueError` | Worktree path check | Legitimate — `.relative_to()` check |
| `finalize_repo.py:125` | `except JSONDecodeError` | Malformed gh output | Review — should this be fatal? |
| `finalize_repo.py:160,162` | `except FileNotFoundError/ConfigError` | Config handling | Legitimate — optional config |
| `commit.py:155,158` | `except FileNotFoundError/ConfigError` | Config handling | Legitimate — optional config |
| `ensure_label.py:73` | `except Exception` | Broad catch | Review — what is this suppressing? |
| `config.py:65` | `except TOMLDecodeError` | Config parse error | Legitimate — re-raises as ConfigError |
| `docker.py:76` | `except OSError` | Reading .git file | Legitimate — worktree detection fallback |
| `docker.py:154` | `except (FileNotFoundError, TimeoutExpired)` | Docker daemon check | Legitimate — system boundary |

- [ ] **Step 2: Review flagged items**

For each "Review" item above, read the surrounding code to determine whether the exception handler is justified. If it suppresses an error without justification, either:
- Convert to fatal (raise or return error code), or
- Add a comment explaining why suppression is correct.

Read the relevant code sections:
- `check_pr_merge.py` around line 173
- `docker_test.py` around line 63
- `finalize_repo.py` around line 125
- `ensure_label.py` around line 73

- [ ] **Step 3: Apply fixes if needed**

For any handler that should be fatal, update the code and its tests. For any handler that is correctly suppressing, add a brief comment explaining why (if one doesn't already exist).

- [ ] **Step 4: Run full test suite**

Run: `st-docker-run -- uv run st-validate-local`
Expected: ALL PASS

- [ ] **Step 5: Commit (if changes were made)**

```
git add -A
git commit -m "refactor: audit and fix catch-and-suppress patterns

Convert unjustified exception suppression to fatal errors.
Document justified suppression with comments.

Ref #427"
```

---

### Task 7: Final validation

- [ ] **Step 1: Run full validation**

Run: `st-docker-run -- uv run st-validate-local`
Expected: ALL PASS — lint, typecheck, tests, audit.

- [ ] **Step 2: Verify no shutil.which guard patterns remain (codebase-wide)**

Run: `grep -rn "shutil.which" src/ tests/ --include='*.py'`
Expected: Only `validate_local.py` (legitimate discovery), `test_validate_local.py` (tests for that discovery), and `test_pre_commit_gate.py` (direct call to locate bash).

- [ ] **Step 3: Verify no pip install references remain (codebase-wide)**

Run: `grep -rn "pip.install\|pip_install" src/ tests/ docs/ CLAUDE.md --include='*.py' --include='*.md' --include='*.toml'`
Expected: No standard-tooling references. (General Python documentation about pip in other contexts is fine.)
