# Implementation Plan: Decouple standard-tooling from dev container images

**Status:** Draft
**Spec:** [`docs/specs/host-level-tool.md`](../specs/host-level-tool.md)
(this plan rewrites Principle 6 and the "Dev container image policy"
section of the spec)
**Issue:** [#362](https://github.com/wphillipmoore/standard-tooling/issues/362)
**Last updated:** 2026-04-29

## Problem

Every `standard-tooling` release triggers a full rebuild of all dev
container images in `standard-tooling-docker` (~15-20 minutes). The
images carry a pre-baked copy of `standard-tooling` installed at build
time via `docker/common/standard-tooling-{uv,pip}.dockerfile` fragments.
A `repository_dispatch` event fires on each release, and a verification
workflow polls for up to 25 minutes to confirm the images carry the new
version.

Python repos do not use the pre-baked copy — they install
`standard-tooling` dynamically via `[tool.uv.sources]` dev deps and
`uv sync --group dev`. The pre-bake exists solely for non-Python
consumers (Go, Ruby, Rust, Java, docs repos) that have no native
package manager integration.

## Decision

Remove `standard-tooling` from dev container images entirely. Install
it at container runtime for non-Python repos, transparently, inside
`st-docker-run`.

## Mechanism

`st-docker-run` already knows the repo's language via
`detect_language()`. For non-Python repos, it builds (or reuses) a
per-branch cached Docker image with standard-tooling pre-installed,
then runs the user's command directly against that image:

```text
# What the user runs:
st-docker-run -- st-validate-local

# First invocation on a branch (non-Python): auto-builds cached image
#   1. docker create + docker start: pip install standard-tooling + warmup
#   2. docker commit → tagged image for this branch + hash
#   3. Runs the command against the cached image

# Subsequent invocations: uses cached image directly (no install)
# Hash mismatch (lockfile or st-config.toml changed): rebuilds automatically

# Python repos — unchanged (use dev deps via uv sync):
uv run st-validate-local
```

### Version pin: `st-config.toml`

Each consuming repo declares its standard-tooling version in a new
`st-config.toml` file at the repo root:

```toml
[standard-tooling]
tag = "v1.4"
```

`st-docker-run` reads this file and uses the tag for the runtime
install. This is a **requirement**, not a fallback — `st-docker-run`
errors if the file or the `standard-tooling.tag` field is missing.

Parsed with `tomllib` (stdlib since Python 3.11) — no new
dependencies.

This change introduces `st-config.toml` as the first step toward a
unified per-repo configuration file for all `st-*` tooling. Everything
currently parsed from `docs/repository-standards.md` via
`repo_profile.py` (repository type, versioning scheme, branching model,
primary language, validation policy, etc.) will migrate into
`st-config.toml` in follow-up work. This plan implements only the
`standard-tooling.tag` field; the full migration is tracked separately.

**Why `st-config.toml`, not `importlib.metadata`:** The consuming repo
must own the version pin, not the host. `importlib.metadata` derives
the tag from the host-installed version, which means a host upgrade
silently changes what every repo installs in the container. An explicit
config file gives each repo durable, version-controlled control over
its standard-tooling pin.

**Bootstrapping:** As part of Phase 2, every consuming repo gets an
`st-config.toml` committed with `tag = "v1.4"`. This is a hard
cutover, not a gradual migration — all repos get the file at the same
time the images lose their pre-bake.

### Per-branch image caching: `st-docker-cache`

Related:
[#354](https://github.com/wphillipmoore/standard-tooling/issues/354)

Without caching, every `st-docker-run` invocation pays the full cost
of installing standard-tooling (~5-10s) and, for compiled languages,
rebuilding the entire dependency tree (minutes for Rust). Over the
course of a development cycle with dozens of validation runs, this
adds up significantly.

This plan introduces `st-docker-cache` — a new command that manages
per-branch Docker images. It builds a derived image on top of the
base dev image, pre-loaded with standard-tooling and project
dependencies. `st-docker-run` consumes the cached image when
available, falling back to the base image (with runtime install) when
no cache exists.

#### Two-command split

| Command | Responsibility |
|---|---|
| **`st-docker-cache`** | Build, rebuild, and clean up per-branch Docker images. Manages the image lifecycle. |
| **`st-docker-run`** | Run a command in a container. Uses the cached image if one exists for the current branch; otherwise falls back to the base image with runtime install. |

This keeps `st-docker-run` focused on execution and `st-docker-cache`
focused on image management. The two communicate through a naming
convention for Docker image tags.

#### Image naming

```text
dev-python:3.14--feature-362-decouple--a1b2c3d4
│               │                      │
│               │                      └─ lockfile hash (first 8 chars)
│               └─ branch name (sanitized)
└─ base image tag
```

`st-docker-run` looks for an image matching the current branch. If
found, it uses it directly (no runtime install, no dep warmup). If
not found, it auto-builds a cached image (installing standard-tooling
and running warmup commands), then uses it.

#### Cache invalidation via lockfile hash

`st-docker-cache` computes a hash over a set of cache-sensitive files.
The files are determined by the project language (auto-detected or
declared in `st-config.toml`):

| Language | Cache-sensitive files |
|---|---|
| Python | `uv.lock`, `st-config.toml` |
| Ruby | `Gemfile.lock`, `st-config.toml` |
| Rust | `Cargo.lock`, `st-config.toml` |
| Go | `go.sum`, `st-config.toml` |
| Java | `pom.xml`, `st-config.toml` |
| Unknown | `st-config.toml` only (use `docker.cache-files` override for custom projects) |

`st-config.toml` is always included because a change to
`standard-tooling.tag` requires reinstalling standard-tooling in
the cached image.

On each `st-docker-cache build` invocation:

1. Compute the hash of the cache-sensitive files.
2. Check if a cached image with that hash already exists.
3. If yes, nothing to do (cache is current).
4. If no, build a new cached image: start from base, install
   standard-tooling, run the language-specific dep warmup, tag with
   the new hash, remove the old cached image for this branch.

The edge case of the rolling tag changing (e.g., `v1.4` now points
to a newer patch) without `st-config.toml` changing is acceptable to
miss. The next explicit tag bump in `st-config.toml` catches it.

#### Language-specific warmup commands

Each language has a default dep-install command that `st-docker-cache`
runs to warm the image:

| Language | Default warmup |
|---|---|
| Python | `uv sync --group dev` |
| Ruby | `bundle install --jobs 4` |
| Rust | `cargo fetch && cargo build --lib` |
| Go | `go mod download && go build ./...` |
| Java | `./mvnw dependency:resolve` |

For non-Python repos, standard-tooling is installed via pip before the
warmup. For Python repos, standard-tooling comes in via `uv sync` as
part of the warmup.

The default can be overridden in `st-config.toml`:

```toml
[standard-tooling]
tag = "v1.4"

[docker]
warmup = "cargo fetch && cargo build --release --lib"
cache-files = ["Cargo.lock", "st-config.toml"]
```

Auto-detection is the default; `st-config.toml` is the override. Most
repos need zero additional config.

#### Lifecycle integration

| Event | Action | Who |
|---|---|---|
| Branch created | `st-docker-cache build` | Agent (branch-workflow skill) or manual |
| Normal work | `st-docker-run` uses cached image | Automatic |
| Deps change | `st-docker-cache build` detects hash mismatch, rebuilds | Manual or hook-triggered |
| Branch cleaned up | `st-docker-cache clean` | `st-finalize-repo` or manual |

`st-finalize-repo` already handles branch cleanup. Adding
`st-docker-cache clean` to its teardown sequence is a natural
extension.

#### `st-docker-cache` subcommands

```text
st-docker-cache build     # Build/rebuild cached image for current branch
st-docker-cache clean     # Remove cached image for current branch
st-docker-cache status    # Show cached image info (exists, hash, age)
st-docker-cache clean-all # Remove all st-docker-cache images (nuclear option)
```

#### Fallback behavior

When no cached image exists, `st-docker-run` falls back to the base
image with the runtime `pip install` wrapping described earlier in
this plan. This means:

- Repos that never run `st-docker-cache build` still work — they just
  pay the runtime install cost on every invocation.
- A missing or stale cache is a performance issue, not a correctness
  issue.

Cached images are local to the developer's Docker daemon. CI always
uses the base image with runtime install — ephemeral runners cannot
meaningfully benefit from local image caching.

### Env var overrides

| Variable | Effect |
|---|---|
| `ST_DOCKER_INSTALL_TAG` | Override the tag from `st-config.toml` (e.g., for testing a pre-release) |
| `ST_DOCKER_SKIP_INSTALL` | Set to `1` to skip the runtime install entirely (escape hatch for custom images) |

### Known limitations

**Unauthenticated HTTPS for runtime install.** The runtime `pip
install` uses unauthenticated HTTPS to clone `standard-tooling` from
GitHub, matching the pattern used by the current image build
fragments. This works because `standard-tooling` is a public
repository. If the repository ever becomes private, the install URL
must embed credentials (e.g.,
`git+https://x-access-token:${GH_TOKEN}@github.com/...`).

## Scope

### What changes

| Repo | Change |
|---|---|
| **standard-tooling** | Add `st-config.toml` reader, `st-docker-cache` command, runtime install wrapping in `docker.py` and `docker_run.py`; update `st-finalize-repo` to clean cached images; remove docker dispatch from `publish.yml`; delete `verify-docker-images.yml`; update spec and docs |
| **standard-tooling-docker** | Delete both `standard-tooling-*.dockerfile` fragments; remove `@include` lines from all 6 Dockerfiles; remove `repository_dispatch` trigger from `docker-publish.yml`; add `st-config.toml` |
| **standard-tooling-plugin** | Add `st-config.toml` |
| **standard-actions** | Add `st-config.toml` |
| **All other consuming repos** | Add `st-config.toml` |

### What does NOT change

- **`docker_test.py`** — test commands (`go test`, `bundle exec rake`,
  etc.) do not invoke `st-*` tools. No wrapping needed.
- **`docker_docs.py`** — runs `mkdocs`, not `st-*` tools.
- **`python-support.dockerfile`** — still needed in non-Python images
  for `pip` (used by the runtime install) and `yamllint` (used directly
  by `st-validate-local-common-container`).
- **Python repo workflows** — `uv sync --group dev` continues to
  install `standard-tooling` into `.venv` inside the container.

### What gets removed

| Repo | File/Section | Reason |
|---|---|---|
| standard-tooling | `publish.yml` lines 66-91 (dispatch steps) | No image rebuild to trigger |
| standard-tooling | `verify-docker-images.yml` (entire file) | Nothing to verify in images |
| standard-tooling-docker | `docker/common/standard-tooling-uv.dockerfile` | No longer baked into images |
| standard-tooling-docker | `docker/common/standard-tooling-pip.dockerfile` | No longer baked into images |
| standard-tooling-docker | `@include` directives in 6 Dockerfile templates | Fragments deleted |
| standard-tooling-docker | `repository_dispatch` trigger in `docker-publish.yml` | No longer needed |

## Phases

### Sequencing

```text
Phase 1  (st-config.toml + runtime install wrapping — standard-tooling)
Phase 1b (st-docker-cache command — standard-tooling)
    │
    ▼
  release + host upgrade
    │
    ├──► Phase 2b (bootstrap st-config.toml — all consuming repos)
    ├──► Phase 3  (remove dispatch/verify — standard-tooling)
    │
    ▼
  Phase 2b complete for all active repos
    │
    └──► Phase 2  (strip images — standard-tooling-docker)
    │
    ▼
Phase 4 (update spec and docs — standard-tooling)
```

Phase 1 and 1b can be developed in parallel (separate branches);
Phase 1 must merge first (1b depends on `config.py` and the runtime
install fallback). Together they provide both correctness (any repo
works without a cache) and speed (cached repos skip all install
overhead).

Phase 1 must release before Phases 2/2b/3 start. The new
`st-docker-run` must be on the host before images lose their
pre-baked copy and before repos are required to have `st-config.toml`.

Phase 1 is backward-compatible: the `pip install` wrapping runs
against current images and no-ops (the pre-baked version satisfies
the requirement). `st-config.toml` is added to this repo in Phase 1
but is only required by the new wrapping code path — Python repos
(like this one) skip the install, so missing config in other repos
does not break until Phase 2b lands.

Phase 2b must complete for all actively-used non-Python repos before
Phase 2 merges. Without `st-config.toml`, the runtime install path
errors — so stripping the pre-bake before config files exist breaks
non-Python repos. Phase 3 is independent and can run in parallel
with 2b.

Phase 4 is a docs-only follow-up after the functional work lands.

### Phase 1: Add runtime install to `st-docker-run`

**Repo:** standard-tooling
**Branch type:** feature

#### 1.1 Implement `st-config.toml` reader

File: `src/standard_tooling/lib/config.py` (new)

Minimal config reader for `st-config.toml`. Reads the file from the
repo root, parses TOML, returns a typed config object. For this phase,
the only field is `standard-tooling.tag`.

```python
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
    tag = os.environ.get("ST_DOCKER_INSTALL_TAG")
    if tag:
        return tag
    config = read_st_config(repo_root)
    st = config.get("standard-tooling", {})
    tag = st.get("tag")
    if not tag:
        raise SystemExit(
            f"ERROR: {_CONFIG_FILE} missing 'standard-tooling.tag' field."
        )
    return tag
```

#### 1.2 Add wrapping functions to `docker.py`

File: `src/standard_tooling/lib/docker.py`

Add at module level:

```python
import shlex
from standard_tooling.lib.config import st_install_tag

_ST_GIT_URL = "https://github.com/wphillipmoore/standard-tooling"

def needs_runtime_st_install(lang: str) -> bool:
    if os.environ.get("ST_DOCKER_SKIP_INSTALL") == "1":
        return False
    return lang != "python"

def wrap_command_for_st_install(
    command: list[str], lang: str, repo_root: Path,
) -> list[str]:
    if not needs_runtime_st_install(lang):
        return command
    tag = st_install_tag(repo_root)
    install = (
        f"pip install --quiet"
        f" 'standard-tooling @ git+{_ST_GIT_URL}@{tag}'"
    )
    return ["bash", "-c", f"{install} && {shlex.join(command)}"]
```

#### 1.3 Call the wrapper in `docker_run.py`

File: `src/standard_tooling/bin/docker_run.py`

After `detect_language` and before `build_docker_args`:

```python
from standard_tooling.lib.docker import wrap_command_for_st_install

container_command = wrap_command_for_st_install(command, lang, repo_root)
```

Pass `container_command` (not `command`) to `build_docker_args`.

Add diagnostic output:

```text
Language: go
Image:    ghcr.io/wphillipmoore/dev-go:1.26
Install:  runtime (pip install standard-tooling@v1.4)
Command:  st-validate-local
---
```

For Python repos: `Install:  skipped (Python repos use dev deps)`.

#### 1.4 Update `_USAGE` in `docker_run.py`

Add `ST_DOCKER_INSTALL_TAG` and `ST_DOCKER_SKIP_INSTALL` to the
environment variables section.

#### 1.5 Write tests

File: `tests/standard_tooling/test_config.py` (new)

- Missing `st-config.toml` → `SystemExit`
- Missing `standard-tooling.tag` field → `SystemExit`
- Valid file returns tag string
- `ST_DOCKER_INSTALL_TAG` env var overrides file

File: `tests/standard_tooling/test_docker.py`

- `needs_runtime_st_install("go")` → `True`
- `needs_runtime_st_install("ruby")` → `True`
- `needs_runtime_st_install("rust")` → `True`
- `needs_runtime_st_install("java")` → `True`
- `needs_runtime_st_install("")` → `True`
- `needs_runtime_st_install("python")` → `False`
- `ST_DOCKER_SKIP_INSTALL=1` → `False` for all languages
- `wrap_command_for_st_install(["st-validate-local"], "go", repo_root)`
  → wraps with `bash -c "pip install ... && st-validate-local"`
- `wrap_command_for_st_install(["uv", "run", "st-validate-local"], "python", repo_root)`
  → returns input unchanged
- Multi-token command joins correctly via `shlex.join`

File: `tests/standard_tooling/test_docker_run.py`

- Non-Python repo with `st-config.toml`: `main(["--", "st-validate-local"])`
  produces docker args containing `bash -c "pip install ... && st-validate-local"`
- Python repo: `main(["--", "uv", "run", "st-validate-local"])` produces
  docker args ending with `uv run st-validate-local` (no wrapping)

#### 1.6 Add `st-config.toml` to this repo

File: `st-config.toml` (new, at repo root)

```toml
[standard-tooling]
tag = "v1.4"
```

This repo is a Python project, so the runtime install is skipped
during normal validation. But the config file should be present for
consistency and to exercise the reader in tests.

#### 1.7 Validate and release

Run `st-docker-run -- uv run st-validate-local` (100% coverage
required). Cut a patch release. Upgrade the host install.

### Phase 1b: Add `st-docker-cache` command

**Repo:** standard-tooling
**Branch type:** feature
**Can develop in parallel with Phase 1; must merge after Phase 1**

#### 1b.1 Implement `st-docker-cache` CLI

File: `src/standard_tooling/bin/docker_cache.py` (new)

Entry point: `st-docker-cache`. Subcommands:

- **`build`** — Compute the lockfile hash for the current branch.
  If no cached image exists with that hash, build one: `docker run`
  from the base image with the repo mounted, `pip install
  standard-tooling@<tag>`, run the language-specific warmup command,
  then `docker commit` the container as a new image tagged with the
  naming convention. Remove the old cached image for this branch if
  the hash changed.
- **`clean`** — Remove the cached image for the current branch.
- **`status`** — Print whether a cached image exists, the hash, and
  the image age.
- **`clean-all`** — Remove all `st-docker-cache`-managed images.

#### 1b.2 Add cache-aware image selection to `docker.py`

File: `src/standard_tooling/lib/docker.py`

Add a function that checks whether a cached image exists for the
current branch and returns it. `st-docker-run` calls this before
falling back to the base image:

```python
def cached_image(repo_root: Path, branch: str, lang: str) -> str | None:
    """Return the cached image tag if one exists, else None."""
    ...
```

#### 1b.3 Wire cache lookup into `docker_run.py`

File: `src/standard_tooling/bin/docker_run.py`

Before the existing `default_image()` call, check for a cached image.
If found, use it directly (skip runtime install wrapping). Diagnostic
output:

```text
Language: go
Image:    dev-go:1.26--feature-362-decouple--a1b2c3d4 (cached)
Command:  st-validate-local
---
```

#### 1b.4 Add cache cleanup to `st-finalize-repo`

File: `src/standard_tooling/bin/finalize_repo.py`

After branch deletion, call `st-docker-cache clean` for the deleted
branch (or invoke the cleanup function directly).

#### 1b.5 Write tests

File: `tests/standard_tooling/test_docker_cache.py` (new)

- Hash computation deterministic for same inputs
- Hash changes when lockfile content changes
- Hash changes when `st-config.toml` changes
- Correct lockfile selected per language
- `build` creates a Docker image with expected tag
- `clean` removes the image for the current branch
- `clean-all` removes all managed images
- `status` reports correct state
- Cache hit in `docker_run.py` skips runtime install wrapping
- Cache miss in `docker_run.py` falls back to runtime install

#### 1b.6 Register console script

File: `pyproject.toml`

Add `st-docker-cache` to `[project.scripts]`.

### Phase 2: Strip standard-tooling from images

**Repo:** standard-tooling-docker
**Branch type:** feature
**Depends on:** Phase 1 released and host-upgraded

#### 2.1 Delete dockerfile fragments

Delete:
- `docker/common/standard-tooling-uv.dockerfile`
- `docker/common/standard-tooling-pip.dockerfile`

#### 2.2 Remove `@include` directives

In each Dockerfile template:
- `base/Dockerfile.template`: remove `# @include common/standard-tooling-uv.dockerfile`
- `python/Dockerfile.template`: remove `# @include common/standard-tooling-uv.dockerfile`
- `go/Dockerfile.template`: remove `# @include common/standard-tooling-pip.dockerfile`
- `ruby/Dockerfile.template`: remove `# @include common/standard-tooling-pip.dockerfile`
- `rust/Dockerfile.template`: remove `# @include common/standard-tooling-pip.dockerfile`
- `java/Dockerfile.template`: remove `# @include common/standard-tooling-pip.dockerfile`

#### 2.3 Keep `python-support.dockerfile`

No changes. Non-Python images still need `python3`, `pip`, and
`yamllint`.

#### 2.4 Remove `repository_dispatch` trigger

File: `.github/workflows/docker-publish.yml`

Remove:

```yaml
repository_dispatch:
  types: [standard-tooling-released]
```

Images rebuild on their own schedule (push to main, manual trigger),
no longer on standard-tooling releases.

#### 2.5 Verify

- All 6 images build successfully
- `pip` is available in all images
- `st-validate-local` is NOT on PATH (confirming removal)
- `st-docker-run -- st-validate-local` works against a non-Python
  repo (runtime install provides `st-*`)

### Phase 2b: Bootstrap `st-config.toml` in all consuming repos

**Depends on:** Phase 1 released and host-upgraded
**Can run in parallel with Phase 3**
**Must complete before Phase 2**

Add `st-config.toml` to every consuming repo that uses `st-docker-run`.
This is a hard cutover — all repos get the file at the same time.

File content (identical across all repos):

```toml
[standard-tooling]
tag = "v1.4"
```

Repos to bootstrap:

- `standard-tooling` (done in Phase 1.6)
- `standard-tooling-plugin`
- `standard-tooling-docker`
- `standard-actions`
- `standards-and-conventions`
- `the-infrastructure-mindset`
- `ai-research-methodology`
- All `mq-rest-admin-*` repos (when they re-enter active development)

Each repo gets a single commit adding the file. No other changes
needed — `st-docker-run` reads the file transparently.

#### Follow-up: migrate `docs/repository-standards.md` into `st-config.toml`

File a separate issue to migrate all fields currently parsed from
`docs/repository-standards.md` by `repo_profile.py` into
`st-config.toml`. This includes: `repository_type`, `versioning_scheme`,
`branching_model`, `release_model`, `supported_release_lines`,
`primary_language`, `canonical_local_validation_command`, and the
validation policy fields. The migration replaces the markdown-based
config with structured TOML and retires `repo_profile.py`'s markdown
parser. Out of scope for this plan.

### Phase 3: Remove dispatch and verification pipeline

**Repo:** standard-tooling
**Branch type:** chore
**Can run in parallel with Phase 2b**

#### 3.1 Remove docker dispatch from `publish.yml`

File: `.github/workflows/publish.yml`

Remove:
- "Generate cross-repo token for docker dispatch" step (and its
  `actions/create-github-app-token` usage — verify the same secrets
  are not used by the bump PR step before removing)
- "Trigger standard-tooling-docker rebuild" step

Keep:
- "Generate app token for bump PR" step (uses the same secrets for a
  different purpose)

#### 3.2 Delete `verify-docker-images.yml`

File: `.github/workflows/verify-docker-images.yml`

Delete the entire file.

### Phase 4: Update spec and docs

**Repo:** standard-tooling
**Branch type:** docs

#### 4.1 Update `host-level-tool.md`

File: `docs/specs/host-level-tool.md`

Key sections to rewrite:

- **Principle 6** (line 84-89): change from "The dev container image
  tracks the rolling minor tag and rebuilds on every standard-tooling
  release" to "`st-docker-run` transparently installs standard-tooling
  at container runtime for non-Python repos. The version matches the
  host-installed minor."
- **Deployment targets table** (line 93-97): replace the "Dev container
  image" row with the runtime install mechanism.
- **Dev container image policy** (lines 326-359): rewrite. Images no
  longer contain standard-tooling. Non-Python images require
  `python3` and `pip` via `python-support.dockerfile`.
- **Image rebuild cadence tradeoff** (lines 725-738): remove or
  rewrite. There is no longer a rebuild-freshness window.
- **Non-Python consumers** (lines 316-322): update to describe the
  runtime install mechanism instead of image pre-bake.
- **Acceptance criteria** (lines 743-784): remove items related to
  image pre-bake and automated rebuild. Add items for runtime install.

#### 4.2 Update `CLAUDE.md`

File: `CLAUDE.md`

Update the Consumption Model table (lines 229-235):
- Replace the "Dev container image" row with a note that non-Python
  repos get standard-tooling injected at runtime by `st-docker-run`.

#### 4.3 Update `host-level-tool-plan.md`

File: `docs/plans/host-level-tool-plan.md`

Add a note that Phase 3 of the original plan (image policy) has been
superseded by this plan.

## Backward compatibility

Phase 1 is fully backward-compatible. The runtime install wrapping
runs `pip install` inside containers that already have standard-tooling
pre-baked. The install either no-ops (same version) or upgrades
(newer version on the tag). No consumer-visible behavior change.

The one risk window: a developer with the OLD `st-docker-run`
(pre-wrapping) pulling NEW images (without pre-bake). Non-Python repos
would fail because `st-*` is not on PATH and nothing installs it.

Mitigation: the fleet-of-one model means a single developer upgrading
in sequence. Phase 1 releases → host upgrade → Phase 2 strips images.
The upgrade one-liner is in the release notes.

## Rejected alternatives

### Entrypoint script in the Docker image

Add a `/docker-entrypoint.sh` that runs `pip install standard-tooling`
on container start. Rejected: adds complexity to the image build, moves
the install logic out of `st-docker-run` where it belongs, and still
requires the image to know the version tag.

### Per-repo `scripts/dev/setup.sh`

Each non-Python repo provides an explicit setup step. Rejected: adds
boilerplate to every non-Python consumer, violates the "no repo-specific
logic" constraint, and `st-docker-run` already has the context to do
it transparently.

### `uv pip install` in the base image

Keep using `uv` for the install in images that have it (base, python).
Rejected: the whole point is to remove standard-tooling from image
builds. Runtime install via `pip` is available in all images via
`python-support.dockerfile`.

### `importlib.metadata` for version derivation

Derive the rolling tag from the host-installed standard-tooling
version at runtime. Rejected: the consuming repo must own the version
pin, not the host. A host upgrade would silently change what every
repo installs in the container. `st-config.toml` gives each repo
durable, version-controlled control.

### Named Docker volume for pip cache

Mount a persistent Docker volume (`st-pip-cache:/root/.cache/pip`) to
cache the pip download across container runs. Rejected: caches only
the download, not the installed state. The per-branch image caching
via `st-docker-cache` (Phase 1b) captures all installed state —
standard-tooling, project deps, compiled artifacts — in a single
derived image, eliminating runtime install overhead entirely.
