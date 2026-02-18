#!/usr/bin/env bash
# Ensure a label exists in a GitHub repository. Creates it if missing.
#
# Usage: ensure-label.sh --repo OWNER/REPO --label NAME
#
# Idempotent: exits 0 whether the label already existed or was created.

set -euo pipefail

repo=""
label=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)  repo="$2";  shift 2 ;;
    --label) label="$2"; shift 2 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$repo" || -z "$label" ]]; then
  echo "Usage: ensure-label.sh --repo OWNER/REPO --label NAME" >&2
  exit 1
fi

if gh label list --repo "$repo" --search "$label" --json name --jq '.[].name' \
    | grep -qx "$label"; then
  echo "Label '$label' already exists in $repo"
else
  gh label create "$label" --repo "$repo"
  echo "Label '$label' created in $repo"
fi
