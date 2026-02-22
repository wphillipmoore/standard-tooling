# sync-tooling.sh

**Path:** `scripts/dev/sync-tooling.sh`

Keeps consuming repositories synchronized with the canonical versions
of all managed scripts in standard-tooling.

## Usage

```bash
scripts/dev/sync-tooling.sh \
  [--check | --fix] [--ref TAG] [--actions-compat]
```

## Arguments

| Argument | Description |
| -------- | ----------- |
| `--check` | Compare local copies (default) |
| `--fix` | Overwrite local copies with canonical versions |
| `--ref TAG` | Tag to sync against (default: latest tag) |
| `--actions-compat` | Also sync lint scripts to actions path |

## Behavior

### Check Mode (default)

1. Clones the canonical standard-tooling at the specified tag (or
   latest).
2. Compares each managed file against the canonical version.
3. Reports `STALE` for modified files and `MISSING` for absent
   files.
4. Exits with code 1 if any files are out of sync.

### Fix Mode

1. Clones the canonical source (same as check mode).
2. Overwrites local copies with canonical versions.
3. Adds missing files and creates directories as needed.
4. Preserves file permissions from the canonical source.

### Self-Update

If `sync-tooling.sh` itself is stale, fix mode updates the script
and re-executes with the same arguments.

### Actions Compatibility

With `--actions-compat`, lint scripts are also synced to
`actions/standards-compliance/scripts/` for use by
`standard-actions`.

## Managed Files

See the [Script Reference overview](../index.md) for the complete
list of 18 managed files.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | All files up to date (check) or sync complete (fix) |
| 1 | Stale files detected (check mode only) |
