# Pushback Review: Decouple standard-tooling from dev container images

**Date:** 2026-04-29
**Spec:** `docs/specs/decouple-st-from-images-plan.md`
**Commit:** fd0eec1 (branch: feature/362-decouple-st-from-images, pre-commit)

## Source Control Conflicts

None — no conflicts with recent changes. All file references
(publish.yml dispatch steps, verify-docker-images.yml, docker.py
functions, docker_run.py) match the current codebase.

## Issues Reviewed

### [1] Phase 2b must complete before Phase 2 — not parallel
- **Category:** Contradiction
- **Severity:** Serious
- **Issue:** The spec said Phases 2, 2b, and 3 are independent and
  can run in parallel. But Phase 2 (strip images) depends on Phase 2b
  (bootstrap st-config.toml): after images lose pre-baked
  standard-tooling, non-Python repos need the runtime install path,
  which requires st-config.toml. Stripping images before config files
  exist breaks non-Python repos.
- **Resolution:** Reordered. Phase 2b is now a prerequisite of
  Phase 2. Updated sequencing diagram and prose. Phase 3 remains
  independent.

### [2] `st-docker-cache build` says "docker build" but should use `docker run` + `docker commit`
- **Category:** Feasibility
- **Severity:** Moderate
- **Issue:** Phase 1b.1 specified `docker build` for creating cached
  images. `docker build` works from a Dockerfile with COPY/RUN layers
  and doesn't support live repo mounts. The warmup commands need the
  repo mounted at /workspace (same layout as st-docker-run). The right
  primitive is `docker run` + `docker commit`.
- **Resolution:** Updated Phase 1b.1 to specify `docker run` from
  the base image with the repo mounted, then `docker commit` the
  container as a new image.

### [3] Per-branch caching is local-only — unstated limitation for CI
- **Category:** Omission
- **Severity:** Moderate
- **Issue:** The fallback section said "CI can choose to build a cache
  at the start of the job" but CI runners are ephemeral — cached
  images don't survive between runs. Leaving this unstated invites
  confusion.
- **Resolution:** Explicitly scoped caching to local development.
  Replaced the CI mention with: "Cached images are local to the
  developer's Docker daemon. CI always uses the base image with
  runtime install."

### [4] Phase 1b's code dependency on Phase 1 is understated
- **Category:** Ambiguity
- **Severity:** Moderate
- **Issue:** Phase 1b said "Can develop in parallel with Phase 1" but
  has a hard code dependency on Phase 1's config.py and docker_run.py
  changes. Development can be parallel; merging cannot.
- **Resolution:** Changed to "Can develop in parallel with Phase 1;
  must merge after Phase 1."

### [5] Unknown language + `st-docker-cache` hash is undefined
- **Category:** Ambiguity
- **Severity:** Minor
- **Issue:** The cache-sensitive files table had no row for unknown
  languages. If `detect_language()` returns "" and no `cache-files`
  override exists, `st-docker-cache` doesn't know what to hash.
- **Resolution:** Added "Unknown" row to table: `st-config.toml` only,
  with note to use `docker.cache-files` override for custom projects.

### [6] `pip install` from git URL uses unauthenticated HTTPS
- **Category:** Feasibility
- **Severity:** Minor
- **Issue:** Runtime install uses unauthenticated HTTPS to clone
  standard-tooling. Works because the repo is public and matches the
  current image build pattern. Would break if the repo became private.
- **Resolution:** Documented as a known limitation. Not a practical
  concern for this repo collection — standard-tooling will remain
  public. If re-implemented for private repos, the install URL would
  need embedded credentials.

## Summary

- **Issues found:** 6
- **Issues resolved:** 6
- **Unresolved:** 0
- **Spec status:** Ready for implementation
