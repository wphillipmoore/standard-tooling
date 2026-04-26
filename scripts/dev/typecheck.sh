#!/usr/bin/env bash
# Container-local typecheck script.  Assumes it is invoked inside the dev
# container by `st-validate-local`.
set -euo pipefail

uv sync --frozen --group dev
uv run mypy src/
