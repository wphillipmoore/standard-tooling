# Implementation Plan: Decouple standard-tooling from dev container images

**Status:** Draft — awaiting `paad:alignment` against the spec
**Spec:** [`docs/specs/decouple-st-from-images-plan.md`](../specs/decouple-st-from-images-plan.md)
**Issue:** [#362](https://github.com/wphillipmoore/standard-tooling/issues/362)
**Pushback review:**
[`paad/pushback-reviews/2026-04-29-decouple-st-from-images-pushback.md`](../../paad/pushback-reviews/2026-04-29-decouple-st-from-images-pushback.md)
**Last updated:** 2026-04-29

## Scope

This plan covers the full implementation of removing pre-baked
`standard-tooling` from dev container images and replacing it with
transparent runtime installation via `st-docker-run`, plus per-branch
image caching via a new `st-docker-cache` command.

Work spans `standard-tooling` (primary), `standard-tooling-docker`,
and all consuming repos, sequenced in six phases:

1. Runtime install wrapping + `st-config.toml` reader (standard-tooling)
1b. `st-docker-cache` command (standard-tooling)
2b. Bootstrap `st-config.toml` in all consuming repos
2. Strip standard-tooling from images (standard-tooling-docker)
3. Remove dispatch/verify pipeline (standard-tooling)
4. Update spec and docs (standard-tooling)

Each phase has observable completion criteria. The plan assumes the
fleet-of-one operational model.

## Out of scope for this plan

- **Full `st-config.toml` migration.** Only the `standard-tooling.tag`
  field is implemented. Migrating all `docs/repository-standards.md`
  fields into `st-config.toml` is tracked separately.
- **CI-level image caching.** Cached images are local to the
  developer's Docker daemon. Ephemeral CI runners always use the base
  image with runtime install.
- **Private repo auth.** The runtime install uses unauthenticated
  HTTPS, matching the current image build pattern. `standard-tooling`
  is a public repository.

## Prerequisites

Before starting Phase 1:

- Current `develop` branch is clean and validated.
- Host `st-docker-run` is at v1.4.x (current).
- Docker daemon is running and dev images are pulled.

---

## Phase 1: Add runtime install to `st-docker-run`

**Repo:** standard-tooling
**Branch:** `feature/362-decouple-st-from-images` (this worktree)
**Issue:** #362

### Step 1.1: Implement `st-config.toml` reader

**File:** `src/standard_tooling/lib/config.py` (new)

Create a minimal config reader with two public functions:

- `read_st_config(repo_root: Path) -> dict` — reads and parses
  `st-config.toml` from the repo root. Raises `SystemExit` if the
  file is missing.
- `st_install_tag(repo_root: Path) -> str` — returns the
  `standard-tooling.tag` value. Checks `ST_DOCKER_INSTALL_TAG` env
  var first (override). Raises `SystemExit` if the field is missing.

Implementation details:

```python
import os
import tomllib
from pathlib import Path

_CONFIG_FILE = "st-config.toml"

def read_st_config(repo_root: Path) -> dict:
    config_path = repo_root / _CONFIG_FILE
    if not config_path.is_file():
        raise SystemExit(
            f"ERROR: {_CONFIG_FILE} not found at {repo_root}.\n"
            f"Every repo must have an {_CONFIG_FILE}."
        )
    with config_path.open("rb") as f:
        return tomllib.load(f)

def st_install_tag(repo_root: Path) -> str:
    override = os.environ.get("ST_DOCKER_INSTALL_TAG")
    if override:
        return override
    config = read_st_config(repo_root)
    st = config.get("standard-tooling", {})
    tag = st.get("tag")
    if not tag:
        raise SystemExit(
            f"ERROR: {_CONFIG_FILE} missing 'standard-tooling.tag' field."
        )
    return tag
```

**Completion:** Unit tests pass (see step 1.5).

### Step 1.2: Add wrapping functions to `docker.py`

**File:** `src/standard_tooling/lib/docker.py`

Add three items at module level:

1. A constant: `_ST_GIT_URL = "https://github.com/wphillipmoore/standard-tooling"`
2. `needs_runtime_st_install(lang: str) -> bool` — returns `False`
   for `"python"` and when `ST_DOCKER_SKIP_INSTALL=1`; `True`
   otherwise.
3. `wrap_command_for_st_install(command: list[str], lang: str,
   repo_root: Path) -> list[str]` — if runtime install is needed,
   returns `["bash", "-c", "pip install --quiet '<url>@<tag>' &&
   <shlex.join(command)>"]`. Otherwise returns command unchanged.

New imports needed: `import shlex` and
`from standard_tooling.lib.config import st_install_tag`.

**Completion:** Unit tests pass (see step 1.5).

### Step 1.3: Wire wrapping into `docker_run.py`

**File:** `src/standard_tooling/bin/docker_run.py`

Changes to `main()`:

1. After `lang = detect_language(repo_root)` (current line 74), add:
   ```python
   from standard_tooling.lib.docker import (
       needs_runtime_st_install,
       wrap_command_for_st_install,
   )
   container_command = wrap_command_for_st_install(command, lang, repo_root)
   ```
   Move this import to the top of the file with the existing docker
   imports.

2. Pass `container_command` instead of `command` to
   `build_docker_args()` (current line 87).

3. Update diagnostic output (lines 77-83). After the existing
   `Image:` line, add an `Install:` line:
   - Non-Python: `Install:  runtime (pip install standard-tooling@<tag>)`
   - Python: `Install:  skipped (Python repos use dev deps)`

### Step 1.4: Update `_USAGE` in `docker_run.py`

**File:** `src/standard_tooling/bin/docker_run.py`

Add two env vars to the `_USAGE` string's environment variables
section:

```text
  ST_DOCKER_INSTALL_TAG  override the standard-tooling version tag from st-config.toml
  ST_DOCKER_SKIP_INSTALL set to 1 to skip the runtime standard-tooling install
```

### Step 1.5: Write tests

#### `tests/standard_tooling/test_config.py` (new)

Test `read_st_config`:
- Missing `st-config.toml` raises `SystemExit` with descriptive message.
- Empty/malformed YAML raises `SystemExit` or returns empty dict
  (verify behavior of `tomllib.load` on edge cases).
- Valid file returns parsed dict.

Test `st_install_tag`:
- Valid config returns the tag string.
- Missing `standard-tooling` key raises `SystemExit`.
- Missing `tag` field raises `SystemExit`.
- `ST_DOCKER_INSTALL_TAG` env var overrides file value (use
  `monkeypatch.setenv`).
- `ST_DOCKER_INSTALL_TAG` env var takes precedence even when file
  is missing (env var is checked first).

Use `tmp_path` fixture to create temporary `st-config.toml` files
for each test case.

#### `tests/standard_tooling/test_docker.py` (existing)

Add tests for `needs_runtime_st_install`:
- `"go"`, `"ruby"`, `"rust"`, `"java"`, `""` all return `True`.
- `"python"` returns `False`.
- With `ST_DOCKER_SKIP_INSTALL=1` set, all languages return `False`.

Add tests for `wrap_command_for_st_install`:
- Non-Python language wraps command with `bash -c "pip install ... &&
  <command>"`.
- Python language returns command unchanged.
- Multi-token commands are joined correctly via `shlex.join` (verify
  quoting of args with spaces).
- `ST_DOCKER_SKIP_INSTALL=1` returns command unchanged regardless
  of language.

Mock `st_install_tag` in wrapping tests to avoid needing a real
`st-config.toml`.

#### `tests/standard_tooling/test_docker_run.py` (existing)

Add integration-level tests for `main()`:
- Non-Python repo with valid `st-config.toml`: verify the docker args
  list contains `bash -c "pip install ... && <command>"`.
- Python repo: verify the docker args end with the original command
  (no wrapping).

These tests need to mock `os.execvp` (already done in existing
tests) and provide a `st-config.toml` in the temp repo fixture.

### Step 1.6: Add `st-config.toml` to this repo

**File:** `st-config.toml` (new, at repo root)

```toml
[standard-tooling]
tag = "v1.4"
```

This repo is a Python project — the runtime install is skipped. The
file exists for consistency and to exercise the reader in tests.

### Step 1.7: Validate

Run `st-docker-run -- uv run st-validate-local`. All tests must
pass with 100% coverage.

**Phase 1 completion criteria:**
- All new and existing tests pass.
- `st-config.toml` exists at repo root.
- `st-docker-run` wraps non-Python commands with `pip install`.
- `st-docker-run` skips wrapping for Python repos.
- `ST_DOCKER_INSTALL_TAG` and `ST_DOCKER_SKIP_INSTALL` work.
- Backward-compatible: wrapping against current images (with
  pre-baked st) no-ops or upgrades harmlessly.

---

## Phase 1b: Add `st-docker-cache` command

**Repo:** standard-tooling
**Branch:** separate feature branch (must merge after Phase 1)
**Issue:** #362 (or sub-issue if needed)

### Step 1b.0: Create branch

Create `feature/362-docker-cache` from `develop` after Phase 1 has
merged. Phase 1b depends on `config.py` and the runtime install
fallback from Phase 1.

### Step 1b.1: Implement cache hash computation

**File:** `src/standard_tooling/lib/docker_cache.py` (new)

Core library functions:

- `_CACHE_FILES: dict[str, list[str]]` — maps language to lockfile
  names. Always includes `st-config.toml`. Unknown language gets only
  `st-config.toml`.

  ```python
  _CACHE_FILES = {
      "python": ["uv.lock", "st-config.toml"],
      "ruby": ["Gemfile.lock", "st-config.toml"],
      "rust": ["Cargo.lock", "st-config.toml"],
      "go": ["go.sum", "st-config.toml"],
      "java": ["pom.xml", "st-config.toml"],
  }
  _DEFAULT_CACHE_FILES = ["st-config.toml"]
  ```

- `cache_sensitive_files(repo_root: Path, lang: str) -> list[Path]`
  — returns resolved paths of cache-sensitive files that exist.
  Checks `st-config.toml` for `docker.cache-files` override first.

- `compute_cache_hash(files: list[Path]) -> str` — SHA-256 over
  sorted file contents, returns first 8 hex chars.

- `_sanitize_branch(branch: str) -> str` — replace `/` with `-`,
  strip characters invalid in Docker tags.

- `cache_image_tag(base_image: str, branch: str, hash: str) -> str`
  — constructs the tag per the naming convention:
  `<base-tag>--<sanitized-branch>--<hash>`.

- `find_cached_image(base_image: str, branch: str) -> tuple[str,
  str] | None` — queries `docker images` for an image matching the
  base+branch pattern. Returns `(tag, hash)` or None.

- `_WARMUP_COMMANDS: dict[str, str]` — default warmup per language.

  ```python
  _WARMUP_COMMANDS = {
      "python": "uv sync --group dev",
      "ruby": "bundle install --jobs 4",
      "rust": "cargo fetch && cargo build --lib",
      "go": "go mod download && go build ./...",
      "java": "./mvnw dependency:resolve",
  }
  ```

- `warmup_command(repo_root: Path, lang: str) -> str | None` —
  returns the warmup command. Checks `st-config.toml` for
  `docker.warmup` override first. Returns None for unknown languages
  with no override.

### Step 1b.2: Implement `st-docker-cache` CLI

**File:** `src/standard_tooling/bin/docker_cache.py` (new)

Entry point with four subcommands via `argparse` sub-parsers:

#### `build` subcommand

1. Determine repo root, language, branch, base image.
2. Compute cache hash from `cache_sensitive_files()`.
3. Check for existing cached image via `find_cached_image()`.
4. If image exists and hash matches: print "Cache is current" and
   exit.
5. If no match: build a new cached image:
   a. Determine install command: for non-Python, `pip install
      --quiet 'standard-tooling @ git+<url>@<tag>'`. For Python:
      skip (warmup handles it).
   b. Determine warmup command from `warmup_command()`.
   c. Construct the full setup command: `<install> && <warmup>`
      (or just `<warmup>` for Python).
   d. Run `docker run --rm` from the base image with the repo
      mounted at `/workspace`, execute the setup command. Capture
      the container ID by using `docker create` + `docker start`
      + `docker wait` instead of `docker run --rm`, so we can
      commit.

      Revised sequence:
      ```
      docker create -v <repo>:/workspace -w /workspace <base> \
          bash -c "<setup_command>"
      docker start -a <container_id>
      docker commit <container_id> <cache_tag>
      docker rm <container_id>
      ```
   e. Remove old cached image for this branch if hash changed
      (`docker rmi <old_tag>`).
6. Print summary: base image, branch, hash, cache tag.

#### `clean` subcommand

1. Find cached image for current branch via `find_cached_image()`.
2. If found: `docker rmi <tag>`. Print confirmation.
3. If not found: print "No cached image for this branch."

#### `status` subcommand

1. Find cached image for current branch.
2. If found: print tag, hash, creation time (from `docker inspect`).
3. If not found: print "No cached image."

#### `clean-all` subcommand

1. List all Docker images matching the `st-docker-cache` naming
   pattern (images with `--` separators in their tags).
2. Remove each one.
3. Print count of removed images.

### Step 1b.3: Add cache-aware image selection to `docker.py`

**File:** `src/standard_tooling/lib/docker.py`

Add function:

```python
def cached_image_for_branch(
    repo_root: Path, lang: str,
) -> str | None:
    """Return cached image tag for current branch, or None."""
    from standard_tooling.lib.docker_cache import find_cached_image
    from standard_tooling.lib import git as _git

    branch = _git.current_branch()
    base = default_image(lang, fallback=True)
    result = find_cached_image(base, branch)
    return result[0] if result else None
```

### Step 1b.4: Wire cache lookup into `docker_run.py`

**File:** `src/standard_tooling/bin/docker_run.py`

In `main()`, after `detect_language()` and before the
`DOCKER_DEV_IMAGE` check:

1. Call `cached_image_for_branch(repo_root, lang)`.
2. If a cached image is returned:
   - Use it as the image (skip `default_image()` and
     `DOCKER_DEV_IMAGE`).
   - Skip runtime install wrapping (the cache already has st
     installed).
   - Print `Image: <tag> (cached)` in diagnostics.
3. If no cached image: fall through to existing logic (base image +
   runtime install wrapping from Phase 1).

### Step 1b.5: Add cache cleanup to `st-finalize-repo`

**File:** `src/standard_tooling/bin/finalize_repo.py`

In the branch deletion loop (after line 202: `deleted.append(branch)`),
add cache cleanup:

```python
# Clean up any cached Docker image for the deleted branch.
from standard_tooling.lib.docker_cache import find_cached_image
from standard_tooling.lib.docker import default_image
# ... determine lang from detect_language if needed, or clean by
# branch name pattern across all base images.
```

Implementation note: `find_cached_image` needs the base image tag,
but at finalize time we may not know the language of the deleted
branch. Simpler approach: add a `clean_branch_images(branch: str)`
function to `docker_cache.py` that removes ALL cached images whose
tag contains `--<sanitized-branch>--`, regardless of base image.
This avoids needing language detection during cleanup.

### Step 1b.6: Register console script

**File:** `pyproject.toml`

Add entry to `[project.scripts]`:

```toml
st-docker-cache = "standard_tooling.bin.docker_cache:main"
```

### Step 1b.7: Write tests

**File:** `tests/standard_tooling/test_docker_cache.py` (new)

Hash computation:
- Same file contents produce same hash.
- Different file contents produce different hash.
- Changing `st-config.toml` changes the hash.
- Missing files are excluded from hash (not an error).
- Correct lockfile selected for each language.
- Unknown language hashes only `st-config.toml`.
- `docker.cache-files` override in `st-config.toml` is respected.

Image tag construction:
- Branch name sanitization (slashes, special chars).
- Tag format matches convention:
  `<base>--<branch>--<hash>`.

Subcommands (mock Docker CLI calls via `subprocess`):
- `build` with no existing cache creates a new image.
- `build` with current cache is a no-op.
- `build` with stale cache removes old, creates new.
- `clean` removes the image for the current branch.
- `clean` with no cache prints message, exits 0.
- `clean-all` removes all managed images.
- `status` reports image info when cache exists.
- `status` reports "no cache" when none exists.

Integration with `docker_run.py`:
- Cache hit: `main()` uses cached image, no runtime install.
- Cache miss: `main()` falls back to base image + runtime install.

Integration with `finalize_repo.py`:
- Branch deletion triggers cache cleanup for that branch.

Warmup command:
- Default warmup selected per language.
- `docker.warmup` override in `st-config.toml` is respected.
- Unknown language with no override returns None (build still
  installs st, just skips warmup).

### Step 1b.8: Validate

Run `st-docker-run -- uv run st-validate-local`. All tests must
pass with 100% coverage.

**Phase 1b completion criteria:**
- `st-docker-cache build` creates a derived image with st + deps.
- `st-docker-cache clean` removes it.
- `st-docker-cache status` reports cache state.
- `st-docker-cache clean-all` removes all cached images.
- `st-docker-run` uses cached image when available.
- `st-docker-run` falls back to runtime install when no cache.
- `st-finalize-repo` cleans cached images for deleted branches.
- All tests pass, 100% coverage.

---

## Release: Phase 1 + 1b

After both phases are merged to `develop`:

1. Run `st-prepare-release` to create the release PR.
2. Merge the release PR. `publish.yml` tags and releases.
3. Merge the auto-bump PR.
4. Upgrade the host install:
   ```bash
   uv tool install 'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.4'
   ```
5. Verify: `st-docker-run --help` shows new env vars;
   `st-docker-cache --help` works.

**Gate:** Phases 2b, 2, and 3 do not start until this release is on
the host.

---

## Phase 2b: Bootstrap `st-config.toml` in all consuming repos

**Depends on:** Phase 1 released and host-upgraded
**Can run in parallel with Phase 3**
**Must complete before Phase 2**

### Step 2b.1: Bootstrap each repo

For each repo in the list below, create a single commit adding
`st-config.toml` at the repo root:

```toml
[standard-tooling]
tag = "v1.4"
```

**Repos (in order):**

1. `standard-tooling-plugin`
2. `standard-tooling-docker`
3. `standard-actions`
4. `standards-and-conventions`
5. `the-infrastructure-mindset`
6. `ai-research-methodology`

For `mq-rest-admin-*` repos: defer until they re-enter active
development. The runtime install path only fires when `st-docker-run`
is used, which only happens during active development.

Each repo: create branch, add file, validate, PR, merge, finalize.

### Step 2b.2: Verify

After all repos have `st-config.toml`:

- Pick a non-Python repo (e.g., `standard-tooling-docker`).
- Run `st-docker-run -- st-validate-local` (or equivalent).
- Confirm the runtime install fires and the command succeeds.

**Phase 2b completion criteria:**
- All actively-used repos have `st-config.toml` committed.
- `st-docker-run` reads the config and installs st at runtime for
  non-Python repos (even though images still have the pre-bake —
  the install is a no-op).

---

## Phase 2: Strip standard-tooling from images

**Repo:** standard-tooling-docker
**Branch type:** feature
**Depends on:** Phase 1 released + Phase 2b complete
**Issue:** create sub-issue in standard-tooling-docker

### Step 2.1: Delete dockerfile fragments

Delete:
- `docker/common/standard-tooling-uv.dockerfile`
- `docker/common/standard-tooling-pip.dockerfile`

### Step 2.2: Remove `@include` directives

In each Dockerfile template, remove the `@include` line:

| File | Line to remove |
|---|---|
| `base/Dockerfile.template` | `# @include common/standard-tooling-uv.dockerfile` |
| `python/Dockerfile.template` | `# @include common/standard-tooling-uv.dockerfile` |
| `go/Dockerfile.template` | `# @include common/standard-tooling-pip.dockerfile` |
| `ruby/Dockerfile.template` | `# @include common/standard-tooling-pip.dockerfile` |
| `rust/Dockerfile.template` | `# @include common/standard-tooling-pip.dockerfile` |
| `java/Dockerfile.template` | `# @include common/standard-tooling-pip.dockerfile` |

### Step 2.3: Verify `python-support.dockerfile` unchanged

Confirm `docker/common/python-support.dockerfile` still installs
`python3-minimal`, `python3-pip`, and `yamllint`. These are still
needed: `pip` for runtime install, `yamllint` for
`st-validate-local-common-container`.

### Step 2.4: Remove `repository_dispatch` trigger

**File:** `.github/workflows/docker-publish.yml`

Remove from the `on:` block:

```yaml
repository_dispatch:
  types: [standard-tooling-released]
```

Images rebuild on push to main and manual trigger only.

### Step 2.5: Build and verify

1. Run `docker/build.sh` to build all 6 images locally.
2. Verify all images build successfully.
3. Verify `pip` is available in all images:
   `docker run --rm <image> pip --version`
4. Verify `st-validate-local` is NOT on PATH:
   `docker run --rm <image> which st-validate-local` (should fail)
5. Verify `st-docker-run -- st-validate-local` works against a
   non-Python repo (runtime install provides `st-*`).

### Step 2.6: PR, merge, finalize

Standard PR workflow. Images rebuild automatically on push to main.

**Phase 2 completion criteria:**
- All 6 images build without standard-tooling pre-baked.
- `pip` available in all images.
- `st-*` tools NOT on PATH in any image.
- `st-docker-run` runtime install provides `st-*` for non-Python
  repos.
- `repository_dispatch` trigger removed.

---

## Phase 3: Remove dispatch and verification pipeline

**Repo:** standard-tooling
**Branch type:** chore
**Can run in parallel with Phase 2b**
**Issue:** #362 or sub-issue

### Step 3.1: Remove docker dispatch from `publish.yml`

**File:** `.github/workflows/publish.yml`

Remove these steps (currently lines 66-91):
- "Generate cross-repo token for docker dispatch" (lines 71-78)
- "Trigger standard-tooling-docker rebuild" (lines 80-91)

**Important:** Verify the `dispatch-token` step's secrets
(`APP_ID`, `APP_PRIVATE_KEY`) are also used by the "Generate app
token for bump PR" step (line 93-99). They are — both use the same
GitHub App. Only remove the `dispatch-token` step and the dispatch
API call, not the secrets themselves.

### Step 3.2: Delete `verify-docker-images.yml`

**File:** `.github/workflows/verify-docker-images.yml`

Delete the entire file (123 lines).

### Step 3.3: Validate and PR

Run `st-docker-run -- uv run st-validate-local`.
Standard PR workflow.

**Phase 3 completion criteria:**
- `publish.yml` no longer fires `repository_dispatch`.
- `verify-docker-images.yml` is gone.
- Release pipeline still works: tag, release, bump PR.

---

## Phase 4: Update spec and docs

**Repo:** standard-tooling
**Branch type:** docs
**Depends on:** Phases 2, 2b, and 3 complete

### Step 4.1: Update `host-level-tool.md`

**File:** `docs/specs/host-level-tool.md`

Sections to rewrite (line numbers approximate — verify before
editing):

1. **Principle 6** (~line 84): change from image-rebuild language to
   runtime install language. New text should say `st-docker-run`
   transparently installs standard-tooling at container runtime for
   non-Python repos.

2. **Deployment targets table** (~line 93): replace the "Dev
   container image (pre-bake)" row. New row describes runtime
   install via `st-docker-run` for non-Python consumers.

3. **Non-Python consumers** (~line 316): update to describe the
   runtime install mechanism instead of image pre-bake.

4. **Dev container image policy** (~line 326): rewrite. Images no
   longer contain standard-tooling. Non-Python images provide
   `python3` and `pip` via `python-support.dockerfile` for the
   runtime install.

5. **Image rebuild cadence tradeoff** (~line 725): remove or
   rewrite. No rebuild-freshness window exists anymore.

6. **Acceptance criteria** (~line 743): remove items related to
   image pre-bake and automated rebuild. Add items for:
   - `st-config.toml` required in all consuming repos.
   - `st-docker-run` transparently installs st at runtime.
   - `st-docker-cache` provides per-branch image caching.

### Step 4.2: Update `CLAUDE.md`

**File:** `CLAUDE.md`

Update the Consumption Model table. Replace the "Dev container
image" row:

| Target | Install mechanism | Who uses it |
|---|---|---|
| **Dev container image** | ~~Pre-baked at image build time~~ Runtime install by `st-docker-run` for non-Python repos | `st-*` inside the container for non-Python consumers |

Also add `st-docker-cache` to the CLI tools list in the Architecture
section.

### Step 4.3: Update `host-level-tool-plan.md`

**File:** `docs/plans/host-level-tool-plan.md`

Add a note that Phase 3 of the original plan (image policy) has been
superseded by the decouple plan.

### Step 4.4: Validate and PR

Run `st-docker-run -- uv run st-validate-local`.
Standard PR workflow.

**Phase 4 completion criteria:**
- All docs reflect the new runtime install model.
- No references to pre-baked standard-tooling in images.
- No references to `repository_dispatch` for image rebuilds.

---

## Follow-up work (out of scope)

File separate issues for:

1. **Migrate `docs/repository-standards.md` into `st-config.toml`.**
   Move all fields parsed by `repo_profile.py` into structured TOML.
   Retire the markdown parser.

2. **Container guardrails (standard-tooling-docker#91).** Make
   host-only tools (`gh`, `git`) fail inside containers with clear
   error messages.

3. **Update branch-workflow and pr-workflow skills** in
   standard-tooling-plugin to invoke `st-docker-cache build` after
   branch creation and recognize `st-config.toml` as a config source.
