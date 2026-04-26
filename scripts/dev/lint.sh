#!/usr/bin/env bash
# Container-local lint script.  Assumes it is invoked inside the dev
# container by `st-validate-local` (itself launched via
# `st-docker-run -- uv run st-validate-local`).
set -euo pipefail

uv sync --frozen --group dev
uv run ruff check
uv run ruff format --check .
