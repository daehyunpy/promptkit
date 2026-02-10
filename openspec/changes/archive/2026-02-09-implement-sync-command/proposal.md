## Why

The `sync` command is the primary user-facing command for promptkit. Users currently must run `promptkit lock` and `promptkit build` separately to go from config to working state. A single `promptkit sync` command composes both operations (fetch → lock → build), matching the workflow pattern of modern package managers like `uv sync` and `npm install`.

## What Changes

- Add `promptkit sync` CLI command that runs lock + build sequentially
- The sync command reuses the existing `LockPrompts` and `BuildArtifacts` use cases — no new domain logic
- Display progress messages showing each phase (locking, building)
- Handle errors from either phase with clear messages

## Capabilities

### New Capabilities
- `sync-command`: CLI command that composes `LockPrompts` + `BuildArtifacts` use cases into a single `promptkit sync` operation

### Modified Capabilities
- `cli-lock-command`: The lock and sync commands share wiring logic (FileSystem, YamlLoader, etc.) which should be extracted to avoid duplication

## Impact

- `source/promptkit/cli.py` — add `sync` command, extract shared wiring
- `tests/test_cli.py` — add CLI-level tests for sync command
- No new domain or infrastructure code needed — sync composes existing use cases
