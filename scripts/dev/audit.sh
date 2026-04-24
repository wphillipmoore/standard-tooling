#!/usr/bin/env bash
# Container-local audit script.  Assumes it is invoked inside the dev
# container by `st-validate-local`.
set -euo pipefail

uv sync --check --frozen --group dev
uv lock --check
