#!/usr/bin/env bash
# List unique repositories linked to a GitHub Project.
#
# Usage: list-project-repos.sh --owner OWNER --project NUMBER
#
# Output: one "owner/repo" per line, sorted, deduplicated.

set -euo pipefail

owner=""
project=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)  owner="$2";   shift 2 ;;
    --project) project="$2"; shift 2 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$owner" || -z "$project" ]]; then
  echo "Usage: list-project-repos.sh --owner OWNER --project NUMBER" >&2
  exit 1
fi

gh project item-list "$project" --owner "$owner" --format json --limit 9999 \
  --jq '.items[].repository' \
  | sort -u \
  | sed 's|https://github.com/||'
