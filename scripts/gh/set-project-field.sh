#!/usr/bin/env bash
# Set a single-select field on a GitHub Project item.
#
# Resolves human-readable field and option names to their IDs automatically.
#
# Usage: set-project-field.sh --owner OWNER --project NUMBER \
#          --item ITEM_ID --field FIELD_NAME --value OPTION_NAME
#
# Output: confirmation message on success.

set -euo pipefail

owner=""
project=""
item_id=""
field_name=""
option_name=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)   owner="$2";       shift 2 ;;
    --project) project="$2";     shift 2 ;;
    --item)    item_id="$2";     shift 2 ;;
    --field)   field_name="$2";  shift 2 ;;
    --value)   option_name="$2"; shift 2 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$owner" || -z "$project" || -z "$item_id" || -z "$field_name" || -z "$option_name" ]]; then
  echo "Usage: set-project-field.sh --owner OWNER --project NUMBER --item ITEM_ID --field FIELD_NAME --value OPTION_NAME" >&2
  exit 1
fi

# Get the global project ID (node ID) needed by item-edit
project_id=$(gh project view "$project" --owner "$owner" --format json --jq '.id')

# Get field ID and option ID from field-list
read -r field_id option_id < <(
  gh project field-list "$project" --owner "$owner" --format json \
    --jq ".fields[] | select(.name == \"$field_name\") | .id + \" \" + (.options[] | select(.name == \"$option_name\") | .id)"
)

if [[ -z "$field_id" ]]; then
  echo "Error: field '$field_name' not found in project $project" >&2
  exit 1
fi

if [[ -z "$option_id" ]]; then
  echo "Error: option '$option_name' not found in field '$field_name'" >&2
  exit 1
fi

gh project item-edit \
  --project-id "$project_id" \
  --id "$item_id" \
  --field-id "$field_id" \
  --single-select-option-id "$option_id"

echo "Set $field_name=$option_name on item $item_id"
