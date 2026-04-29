# Implementation Plan: Decouple standard-tooling from dev container images

**Status:** Phase 1 complete — awaiting release
**Spec:** [`docs/specs/decouple-st-from-images-plan.md`](../specs/decouple-st-from-images-plan.md)
**Issue:** [#362](https://github.com/wphillipmoore/standard-tooling/issues/362)
**Pushback review:**
[`paad/pushback-reviews/2026-04-29-decouple-st-from-images-pushback.md`](../../paad/pushback-reviews/2026-04-29-decouple-st-from-images-pushback.md)
**Last updated:** 2026-04-29

## Scope

This plan covers the full implementation of removing pre-baked
`standard-tooling` from dev container images and replacing it with
cache-first per-branch Docker images built by `st-docker-run`, plus
a new `st-docker-cache` command for explicit cache management.

Work spans `standard-tooling` (primary), `standard-tooling-docker`,
and all consuming repos, sequenced in five phases:

1. Cache-first `st-docker-run` + `st-docker-cache` (standard-tooling) **DONE**
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
- **`docker.warmup` and `docker.cache-files` config overrides.** The
  spec mentions these as future `st-config.toml` fields. Phase 1
  uses hardcoded language-to-file and language-to-warmup mappings.
  Config overrides are deferred to follow-up work if needed.

## Prerequisites

Before starting Phase 1:

- Current `develop` branch is clean and validated.
- Host `st-docker-run` is at v1.4.x (current).
- Docker daemon is running and dev images are pulled.

---

## Phase 1: Cache-first `st-docker-run` + `st-docker-cache`  DONE

**Repo:** standard-tooling
**Branch:** `feature/362-decouple-st-from-images`
**PR:** [#364](https://github.com/wphillipmoore/standard-tooling/pull/364)

Shipped as a single PR. 473 tests, 100% coverage.

### What shipped

| File | Change |
|---|---|
| `src/standard_tooling/lib/config.py` | New. `st-config.toml` reader: `read_st_config()`, `st_install_tag()`. |
| `src/standard_tooling/lib/docker_cache.py` | New. Cache engine: `cache_sensitive_files()`, `compute_cache_hash()`, `find_cached_image()`, `ensure_cached_image()`, `_build_cached_image()`, `clean_branch_images()`. |
| `src/standard_tooling/bin/docker_cache.py` | New. `st-docker-cache` CLI: `build`, `clean`, `status`, `clean-all` subcommands. |
| `src/standard_tooling/bin/docker_run.py` | Modified. Three-way image selection: `DOCKER_DEV_IMAGE` env → Python base → non-Python `ensure_cached_image()`. |
| `src/standard_tooling/bin/finalize_repo.py` | Modified. Calls `clean_branch_images()` after branch deletion (skipped in dry-run). |
| `st-config.toml` | New. `[standard-tooling] tag = "v1.4"`. |
| `pyproject.toml` | Modified. Registered `st-docker-cache` console script. |
| `tests/standard_tooling/test_config.py` | New. 9 tests. |
| `tests/standard_tooling/test_docker_cache.py` | New. 27 tests. |
| `tests/standard_tooling/test_docker_cache_cli.py` | New. 12 tests. |
| `tests/standard_tooling/test_docker_run.py` | Modified. 4 new cache-aware tests. |
| `tests/standard_tooling/test_finalize_repo.py` | Modified. Mocked `clean_branch_images` + 1 new test. |

### Design decision: cache-first, not per-command wrapping

The original plan described wrapping each command with
`bash -c "pip install ... && <command>"`. During implementation this
was rejected in favor of the cache-first approach:

- Install standard-tooling **once** when building the cached image
- Run commands **directly** against the cached image (no wrapping)
- Hash-based invalidation rebuilds automatically when lockfiles or
  `st-config.toml` change

Per-command wrapping was never implemented. The spec's rejected
alternatives section documents this decision.

### Completion criteria (all met)

- `st-config.toml` exists at repo root.
- `st-docker-run` uses cached images for non-Python repos.
- `st-docker-run` skips caching for Python repos.
- `st-docker-cache build|clean|status|clean-all` all work.
- `st-finalize-repo` cleans cached images on branch deletion.
- `ST_DOCKER_INSTALL_TAG` overrides the tag from config.
- `DOCKER_DEV_IMAGE` overrides the base image (skips cache).
- All tests pass, 100% coverage.

---

## Release: Phase 1

After Phase 1 has merged to `develop`:

1. Run `st-prepare-release` to create the release PR.
2. Merge the release PR. `publish.yml` tags and releases.
3. Merge the auto-bump PR.
4. Upgrade the host install:
   ```bash
   uv tool install 'standard-tooling @ git+https://github.com/wphillipmoore/standard-tooling@v1.4'
   ```
5. Verify: `st-docker-run --help` shows `ST_DOCKER_INSTALL_TAG`;
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
development. The cache build path only fires when `st-docker-run`
is used, which only happens during active development.

Each repo: create branch, add file, validate, PR, merge, finalize.

### Step 2b.2: Verify

After all repos have `st-config.toml`:

- Pick a non-Python repo (e.g., `standard-tooling-docker`).
- Run `st-docker-run -- st-validate-local` (or equivalent).
- Confirm the cache build fires and the command succeeds.

**Phase 2b completion criteria:**
- All actively-used repos have `st-config.toml` committed.
- `st-docker-run` reads the config and builds cached images for
  non-Python repos (even though base images still have the pre-bake —
  the install in the cached image is a no-op or harmless upgrade).

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
needed: `pip` for the cached image build, `yamllint` for
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
   non-Python repo (cached image build provides `st-*`).

### Step 2.6: PR, merge, finalize

Standard PR workflow. Images rebuild automatically on push to main.

**Phase 2 completion criteria:**
- All 6 images build without standard-tooling pre-baked.
- `pip` available in all images.
- `st-*` tools NOT on PATH in any image.
- `st-docker-run` cache build provides `st-*` for non-Python repos.
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
   cache-first language. New text should say `st-docker-run`
   transparently builds per-branch cached images with
   standard-tooling installed for non-Python repos.

2. **Deployment targets table** (~line 93): replace the "Dev
   container image (pre-bake)" row. New row describes cached image
   build via `st-docker-run` for non-Python consumers.

3. **Non-Python consumers** (~line 316): update to describe the
   cache-first mechanism instead of image pre-bake.

4. **Dev container image policy** (~line 326): rewrite. Images no
   longer contain standard-tooling. Non-Python images provide
   `python3` and `pip` via `python-support.dockerfile` for the
   cached image build.

5. **Image rebuild cadence tradeoff** (~line 725): remove or
   rewrite. No rebuild-freshness window exists anymore.

6. **Acceptance criteria** (~line 743): remove items related to
   image pre-bake and automated rebuild. Add items for:
   - `st-config.toml` required in all consuming repos.
   - `st-docker-run` transparently builds cached images at runtime.
   - `st-docker-cache` provides explicit cache management.

### Step 4.2: Update `CLAUDE.md`

**File:** `CLAUDE.md`

Update the Consumption Model table. Replace the "Dev container
image" row:

| Target | Install mechanism | Who uses it |
|---|---|---|
| **Dev container image** | ~~Pre-baked at image build time~~ Cache-first build by `st-docker-run` for non-Python repos | `st-*` inside the container for non-Python consumers |

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
- All docs reflect the new cache-first model.
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

4. **`docker.warmup` and `docker.cache-files` config overrides.**
   Allow `st-config.toml` to override the default warmup command and
   cache-sensitive file list per repo. Only needed if the hardcoded
   defaults prove insufficient.
