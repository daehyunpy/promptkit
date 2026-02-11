## Why

After building artifacts with `promptkit build` or `promptkit sync`, there is no way to remove all promptkit-generated files and cached data in a single command. Users must manually delete files from `.cursor/`, `.claude/`, and `.promptkit/cache/` — error-prone since these directories may contain non-promptkit files that should be preserved. A `promptkit clean` command provides a safe, manifest-aware way to reset the project to a pre-build state.

## What Changes

- Add a `promptkit clean` CLI command that removes all promptkit-managed artifacts and optionally clears the plugin cache
- Add a `CleanArtifacts` use case that reads platform manifests and delegates removal
- The command removes:
  - All files listed in `.promptkit/managed/{platform}.txt` manifests
  - The manifest files themselves
  - Empty parent directories left behind (pruning)
  - Optionally: `.promptkit/cache/` directory (with `--cache` flag)
- Non-promptkit files in `.cursor/` and `.claude/` are never touched

## Capabilities

### New Capabilities

- `clean-artifacts`: Use case and domain logic for removing promptkit-managed build artifacts, reading manifests, and pruning empty directories
- `cli-clean-command`: CLI command (`promptkit clean`) with `--cache` flag for optional cache removal

### Modified Capabilities

_(none — this is additive, no existing spec behavior changes)_

## Impact

- **CLI**: New `clean` command added to `cli.py`
- **App layer**: New `CleanArtifacts` use case in `source/promptkit/app/clean.py`
- **Infra layer**: Reuses existing `manifest.py` functions (`read_manifest`, `cleanup_managed_files`)
- **Storage**: Optional deletion of `.promptkit/cache/` directory
- **No breaking changes**: Existing commands and behavior are unaffected
