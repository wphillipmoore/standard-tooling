# Replace pip install with uv tool install and remove guard patterns

**Status:** Approved
**Issues:** [#427](https://github.com/wphillipmoore/standard-tooling/issues/427), [#429](https://github.com/wphillipmoore/standard-tooling/issues/429)
**Related:**
- [standard-tooling-docker#103](https://github.com/wphillipmoore/standard-tooling-docker/issues/103) — add `~/.local/bin` to default PATH in dev container images
- [standard-actions#287](https://github.com/wphillipmoore/standard-actions/issues/287) — guard-pattern cleanup in composite actions
- [standard-tooling-plugin#218](https://github.com/wphillipmoore/standard-tooling-plugin/issues/218) — guard-pattern cleanup in plugin
**Author:** wphillipmoore
**Last updated:** 2026-04-30

## Problem

Two related problems, one root cause:

### PEP 668 breaks non-Python container installs

`docker_cache.py` installs standard-tooling into non-Python dev
containers via `pip install`. Python 3.13 enforces PEP 668, which
rejects `pip install` into externally-managed environments. The cache
build fails, falls back to the base image without `st-*` tools on
PATH, and downstream validation fails. This affects Ruby, Go, Rust,
and Java dev containers.

### Guard-pattern anti-pattern

Multiple files contain `shutil.which` guards and fallback chains
that check whether a tool is installed before calling it. These
guards add complexity without value: the tools are either required
(and should fail loudly if absent) or provided by the dev container
images (and should be assumed present). The guards mask real problems
by silently degrading or reformatting error messages that the natural
failure would have surfaced more clearly.

## Principles

1. **If it's a Python repo, standard-tooling is a dev dependency.**
   The consuming repo declares it in `pyproject.toml`. Nothing to
   install dynamically.
2. **If it's not a Python repo, use `uv tool install`.** The same
   mechanism used for host-level installation.
3. **PATH belongs in the docker images.** Static paths like
   `~/.local/bin` go in the image's shell initialization, not
   scattered across per-invocation code. Tracked in
   standard-tooling-docker#103.
4. **Just run the command.** If a tool should be present, call it.
   If it's missing, let it fail. The natural `FileNotFoundError` or
   shell `command not found` is a better diagnostic than a
   hand-crafted guard message — it points directly at the missing
   command with a traceback.
5. **Validate at setup time, not at every runtime invocation.** If
   installation or configuration should guarantee a tool is present,
   assert that during setup. Don't second-guess it on every call.
6. **Errors are fatal by default.** Do not catch exceptions to
   downgrade them to warnings or silently fall back to a degraded
   path. If an operation fails, propagate the failure. The only
   justified exception-to-warning conversion is one where the
   degraded path is explicitly documented in a comment explaining
   why suppression is correct. The default is propagation, not
   suppression. Silent degradation masks real problems and moves
   failures downstream where the connection to the root cause is
   lost.

## Changes

### 1. `docker_cache.py` — pip to uv migration

**File:** `src/standard_tooling/lib/docker_cache.py`

Replace the `pip install` command in `_build_cached_image` with
`uv tool install`:

```python
# Before
pip_install = f"pip install --quiet 'standard-tooling @ git+{_ST_GIT_URL}@{tag}'"

# After
uv_install = f"uv tool install --quiet 'standard-tooling @ git+{_ST_GIT_URL}@{tag}'"
```

The rest of `_build_cached_image` is unchanged — it builds a setup
command string, creates a container, runs the command, and commits
the image. The `ensure_cached_image` function already gates on
`lang == "python"` and returns the base image unchanged for Python
repos. This is the bifurcation point: Python repos assert the
dev-dep is present; non-Python repos get `uv tool install` via the
cache layer.

No PATH manipulation is needed here. The dev container images will
include `~/.local/bin` on the default PATH
(standard-tooling-docker#103), so `uv tool install`'s console
scripts are found automatically.

Additionally, the two fallback paths in `_build_cached_image` that
return the base image on failure (container creation failure and
cache build failure) are replaced with raised exceptions. The
current fallback silently returns an image without `st-*` tools on
PATH, causing confusing downstream failures. Under principle 6,
these are fatal: if the cache build fails, `st-docker-run` stops
with a clear error pointing at the Docker failure.

### 2. `finalize_repo.py` — remove fallback chain and gh guard

**File:** `src/standard_tooling/bin/finalize_repo.py`

**2a. Post-finalization validation (lines 227-249):** Remove the
three-way fallback that checks `shutil.which("st-docker-run")`, then
`shutil.which("st-validate-local")`, then errors. Replace with a
single unconditional call to `st-docker-run`.

The Python-vs-non-Python distinction for the command inside the
container stays: Python repos run `uv run st-validate-local`,
non-Python repos run bare `st-validate-local`. But the outer
dispatch is always `st-docker-run` — no fallback, no which-check.

If `st-docker-run` isn't installed on the host, `subprocess.run`
raises `FileNotFoundError`. This propagates as a clear signal that
the host install is missing.

The previous fallback to bare `st-validate-local` was migration
scaffolding from pre-Docker days. It has been masking potential
docker issues by silently running validation in a different
environment than the container would provide.

**2b. Docs workflow check (lines 97-99):** Remove the
`shutil.which("gh")` guard. `gh` is a required host tool. Call
`gh run list` directly. If `gh` is not installed,
`subprocess.run` raises `FileNotFoundError` — a clear signal that
the host install is missing.

**2c. Docs workflow failure is fatal:** The current caller treats
a docs workflow failure as a soft warning (exit code 0, "finalize
itself succeeded"). Under principle 6, this changes: if
`_check_docs_workflow_status` returns a failure, `main()` returns
1. The "soft warning" comment and the advisory framing ("Docs
publish is async — investigate before the next merge") are removed.
A failed docs workflow means finalize failed.

The `shutil` import is removed from this file.

### 3. `prepare_release.py` — remove `_ensure_tool`

**File:** `src/standard_tooling/bin/prepare_release.py`

Remove the `_ensure_tool` function and both calls to it:
`_ensure_tool("gh")` in `main()` (line 292) and
`_ensure_tool("git-cliff")` in `_generate_changelog` (line 200).

Both tools are called immediately after via `subprocess.run`: `gh`
via `github.create_pr` and `git-cliff` via `subprocess.run` with
`check=True`. If either tool isn't installed, the subprocess raises
`FileNotFoundError` — a clear, immediate signal. The pre-checks
add no diagnostic value.

The `shutil` import is removed from this file.

### 4. `markdown_standards.py` — remove markdownlint guard

**File:** `src/standard_tooling/bin/markdown_standards.py`

Remove the `shutil.which("markdownlint")` guard that prints
"FATAL: markdownlint not found on PATH" and returns 2. This runs
inside the dev container where markdownlint must be present. If it's
not, `subprocess.run(["markdownlint", ...])` raises
`FileNotFoundError` — a better signal because it includes the
command name and traceback pointing at what's missing. The
hand-crafted error message adds no diagnostic value.

The `shutil` import is removed from this file.

### 5. Host-level-tool spec update

**File:** `docs/specs/host-level-tool.md`

Remove **all** `pip install` references. `uv tool install` is the
only documented install mechanism for standard-tooling. Specific
deletions:

1. **Deployment targets table:** Change the "Non-Python container
   runtime" install mechanism from `pip install` to `uv tool install`.
   Remove the `pip install` alternative from the "Developer host"
   row.
2. **`uv tool install` vs `pip install` comparison table and
   surrounding prose** (lines 144-174): Delete entirely. There is
   no alternative to document.
3. **Cache-first runtime install section:** Update prose referencing
   `pip install` to say `uv tool install`.
4. **standard-tooling-docker migration steps:** Update the migration
   instruction from `pip install` to `uv tool install`.
5. **Upgrade section:** Remove the `pip install` upgrade command and
   "For `pip install` users" block.
6. **Any remaining `pip install` references** found via
   `grep -n "pip install" docs/specs/host-level-tool.md`.

## Out of scope

1. **`validate_local.py`** — the `_find_validator` function uses
   `shutil.which` as a discovery mechanism for optional, per-repo
   validators. This is legitimate: not every repo has every validator,
   and skip-if-absent is the intended design. No changes.
2. **`docker.py:assert_docker_available`** — this is a genuine
   system-boundary check (is the Docker daemon running?), not a
   tool-presence guard. It stays.
3. **Standard-actions guard cleanup** — tracked in
   standard-actions#287. The `standards-compliance` install dance,
   `docs-deploy` detection logic, and `semgrep` bare pip install are
   addressed there.
4. **Plugin guard cleanup** — tracked in
   standard-tooling-plugin#218.
5. **Docker image PATH changes** — tracked in
   standard-tooling-docker#103. This work develops in parallel;
   the images need updating before final cross-language validation.
6. **Renaming `st-validate-local`** — the name is a misnomer now
   that everything is dockerized, but renaming touches every
   consuming repo. Separate concern.

## Dependencies

- **standard-tooling-docker#103** must land (or be developed
  concurrently) so that `~/.local/bin` is on PATH in the dev
  container images. Without this, `uv tool install` places binaries
  where the container can't find them.
- **`uv` must be available in all dev container images.** It already
  is — all current images include `uv`.

## Test strategy

- **Unit tests:** Update existing tests in `test_docker_cache.py` to
  expect `uv tool install` instead of `pip install` in the generated
  command string.
- **Unit tests:** Update `test_docker_cache.py` to assert that
  `_build_cached_image` raises on container creation failure and
  cache build failure (instead of silently returning the base image).
- **Unit tests:** Update `test_finalize_repo.py` to remove
  expectations around the fallback chain.
- **Unit tests:** Update `test_finalize_repo.py` to assert that a
  docs workflow failure causes `main()` to return 1 (not 0).
- **Unit tests:** Verify removal of `_ensure_tool("git-cliff")` call
  in `test_prepare_release.py` — remove any tests that assert the
  pre-check behavior; ensure `_generate_changelog` tests cover the
  `FileNotFoundError` path naturally.
- **Cross-language validation:** Once standard-tooling-docker#103
  lands, exercise the full pipeline on the mq-rest-admin repos
  (Python, Ruby, Go, Rust, Java) to prove the fix works for every
  supported language.

## Acceptance criteria

- [ ] `docker_cache.py`: `pip install` replaced with
      `uv tool install`; `_build_cached_image` raises on container
      creation failure and cache build failure (no silent fallback
      to base image).
- [ ] `finalize_repo.py`: three-way fallback chain replaced with
      unconditional `st-docker-run` call; `shutil.which("gh")` guard
      removed; docs workflow failure returns exit 1 (not 0);
      `shutil` import removed.
- [ ] `prepare_release.py`: `_ensure_tool` function and both calls
      (`_ensure_tool("gh")`, `_ensure_tool("git-cliff")`) removed;
      `shutil` import removed.
- [ ] `markdown_standards.py`: `shutil.which("markdownlint")` guard
      removed; `shutil` import removed.
- [ ] `host-level-tool.md`: all `pip install` references removed,
      including the comparison table and "alternative" framing.
      Verified clean: `grep -rn "pip install" docs/ CLAUDE.md`
      returns no standard-tooling references. `uv tool install` is
      the only documented install mechanism.
- [ ] All unit tests updated per the test strategy (command string
      expectations, fatal error assertions, removed pre-check
      tests).
- [ ] Warning-to-fatal audit: all files under `src/standard_tooling/`
      audited for warning-only error handling (catch-and-warn,
      silent fallback, exit-0-on-failure). Each instance either
      converted to a fatal error or documented with a comment
      explaining why suppression is justified.

## References

- [#427](https://github.com/wphillipmoore/standard-tooling/issues/427) — st-docker-run cache install fails on PEP 668 containers
- [#429](https://github.com/wphillipmoore/standard-tooling/issues/429) — replace pip install with uv tool install in docker cache build
- [standard-tooling-docker#103](https://github.com/wphillipmoore/standard-tooling-docker/issues/103) — add ~/.local/bin to default PATH
- [standard-actions#287](https://github.com/wphillipmoore/standard-actions/issues/287) — guard-pattern cleanup in actions
- [standard-tooling-plugin#218](https://github.com/wphillipmoore/standard-tooling-plugin/issues/218) — guard-pattern cleanup in plugin
- [docs/specs/host-level-tool.md](../specs/host-level-tool.md) — host-level tool distribution spec
