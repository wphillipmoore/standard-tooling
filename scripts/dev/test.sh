#!/usr/bin/env bash
# Container-local test script.  Assumes it is invoked inside the dev
# container by `st-validate-local`.
set -euo pipefail

uv sync --frozen --group dev
uv run pytest --cov=standard_tooling --cov-branch --cov-fail-under=100
