"""Set a single-select field on a GitHub Project item.

Resolves human-readable field and option names to their IDs automatically.
"""

from __future__ import annotations

import argparse
import sys

from standard_tooling.lib import github


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Set a field on a GitHub Project item.")
    parser.add_argument("--owner", required=True, help="GitHub owner")
    parser.add_argument("--project", required=True, help="Project number")
    parser.add_argument("--item", required=True, help="Item ID")
    parser.add_argument("--field", required=True, help="Field name")
    parser.add_argument("--value", required=True, help="Option name")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    project_id = github.read_output(
        "project",
        "view",
        args.project,
        "--owner",
        args.owner,
        "--format",
        "json",
        "--jq",
        ".id",
    )

    jq_filter = (
        f'.fields[] | select(.name == "{args.field}") '
        f'| .id + " " + (.options[] | select(.name == "{args.value}") | .id)'
    )
    ids = github.read_output(
        "project",
        "field-list",
        args.project,
        "--owner",
        args.owner,
        "--format",
        "json",
        "--jq",
        jq_filter,
    )

    parts = ids.split()
    if len(parts) < 1 or not parts[0]:
        print(f"Error: field '{args.field}' not found in project {args.project}", file=sys.stderr)
        return 1
    if len(parts) < 2:
        print(f"Error: option '{args.value}' not found in field '{args.field}'", file=sys.stderr)
        return 1

    field_id, option_id = parts[0], parts[1]

    github.run(
        "project",
        "item-edit",
        "--project-id",
        project_id,
        "--id",
        args.item,
        "--field-id",
        field_id,
        "--single-select-option-id",
        option_id,
    )

    print(f"Set {args.field}={args.value} on item {args.item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
