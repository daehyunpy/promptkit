## Context

promptkit generates platform artifacts into `.cursor/` and `.claude/` during `build` and `sync`. It tracks which files it manages via manifests at `.promptkit/managed/{platform}.txt`. Registry plugins are cached at `.promptkit/cache/plugins/`. Currently there is no command to remove these generated files — users must manually delete them, risking accidental removal of non-promptkit files in the same directories.

The manifest infrastructure (`read_manifest`, `cleanup_managed_files`, `_prune_empty_parents`) already exists and is used by builders pre-build. The clean command reuses this same infrastructure.

## Goals / Non-Goals

**Goals:**
- Provide a single `promptkit clean` command that removes all promptkit-managed artifacts
- Preserve non-promptkit files in `.cursor/` and `.claude/`
- Optionally clear the plugin cache with `--cache` flag
- Follow existing CLI and use case patterns

**Non-Goals:**
- Selective cleaning (per-platform, per-plugin) — clean everything or nothing
- Interactive confirmation prompts — fail-fast, no interactivity
- Cleaning the lock file (`promptkit.lock`) — that's user-managed config

## Decisions

### 1. Reuse existing manifest infrastructure

**Decision**: Call `read_manifest()` and `cleanup_managed_files()` from the existing `manifest.py` module.

**Rationale**: These functions already handle safe file removal, empty directory pruning, and are battle-tested by the build pipeline. No new file removal logic needed.

**Alternative considered**: Walk output directories and remove files matching known patterns. Rejected — fragile, doesn't handle renamed/moved files, manifest approach is already implemented.

### 2. Discover platforms from manifest files, not config

**Decision**: The clean use case reads `.promptkit/managed/` directory to discover which platform manifests exist, rather than loading `promptkit.yaml`.

**Rationale**: Clean should work even if config has been modified or deleted since the last build. The manifests are the ground truth of what was generated. This also avoids requiring a valid config to clean up.

### 3. Delete manifest files after cleanup

**Decision**: After removing all managed artifacts, delete the manifest files themselves (`.promptkit/managed/*.txt`).

**Rationale**: Manifests reference files that no longer exist. Leaving stale manifests would confuse subsequent builds (though builders handle empty manifests gracefully, clean state is cleaner).

### 4. Cache cleaning is opt-in via `--cache` flag

**Decision**: By default, `promptkit clean` only removes build artifacts. The `--cache` flag additionally removes `.promptkit/cache/`.

**Rationale**: Cache is expensive to rebuild (requires network fetches). Most clean scenarios want to reset build output, not re-download everything. Separate flag makes the destructive action explicit.

### 5. Use case lives in app layer, no new domain logic needed

**Decision**: `CleanArtifacts` use case in `source/promptkit/app/clean.py`. No new domain objects.

**Rationale**: Cleaning is an orchestration concern — read manifests, delete files, optionally delete cache. No business rules or invariants to model. The existing manifest module in infra handles the actual file operations.

## Risks / Trade-offs

- **[Risk] Manifest files missing or corrupt** → Clean is a no-op (no files to remove). `read_manifest()` returns empty list for missing files. Acceptable behavior.
- **[Risk] Cache directory doesn't exist** → `shutil.rmtree` with `ignore_errors=True` or guard with existence check. No crash.
- **[Trade-off] No per-platform cleaning** → Simpler implementation, covers 99% of use cases. Users rarely want to clean only one platform.
- **[Trade-off] No dry-run flag** → Keeps scope minimal for MVP. Can add `--dry-run` later if requested.
