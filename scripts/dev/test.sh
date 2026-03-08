#!/usr/bin/env bash
set -euo pipefail

export DOCKER_DEV_IMAGE="${DOCKER_DEV_IMAGE:-ghcr.io/wphillipmoore/dev-python:3.12}"
export DOCKER_TEST_CMD="${DOCKER_TEST_CMD:-uv sync --frozen --group dev && uv run pytest --cov=standard_tooling --cov-branch --cov-fail-under=100}"

if ! command -v st-docker-test >/dev/null 2>&1; then
  echo "ERROR: st-docker-test not found on PATH." >&2
  echo "Install standard-tooling: uv sync in ../standard-tooling" >&2
  exit 1
fi
exec st-docker-test
