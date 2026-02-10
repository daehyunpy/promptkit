## Context

Phases 1-6 are complete. The `LockPrompts` and `BuildArtifacts` use cases both work independently via `promptkit lock` and `promptkit build`. The `sync` command composes them into a single operation, matching the `uv sync` pattern from the technical design.

The CLI currently has duplicated wiring logic between `lock` and `build` commands (both create `FileSystem`, `YamlLoader`, `LockFile`, `PromptCache`). The sync command would triple this duplication.

## Goals / Non-Goals

**Goals:**
- Add `promptkit sync` as the primary user-facing command
- Compose `LockPrompts` + `BuildArtifacts` sequentially in one invocation
- Extract shared wiring to reduce duplication across lock, build, and sync commands
- Display progress messages for each phase

**Non-Goals:**
- No new domain or application layer code — sync is purely CLI composition
- No parallel execution of lock + build (they must run sequentially)
- No partial sync (e.g., lock-only or build-only modes within sync)
- No network retry logic (fail fast per existing error handling strategy)

## Decisions

### 1. Sync as CLI-only composition, not a new use case

The `sync` command will be implemented entirely in `cli.py` by calling `LockPrompts.execute()` followed by `BuildArtifacts.execute()`. No new application-layer `SyncPrompts` use case class is needed.

**Rationale:** The technical design explicitly states `sync = LockPrompts + BuildArtifacts`. Creating a use case class that just delegates to two other use cases adds indirection without value. The CLI layer is the appropriate place for command composition.

**Alternative considered:** Creating `app/sync.py` with a `SyncPrompts` class. Rejected because it would be a thin wrapper with no domain logic — just orchestration that belongs in the CLI.

### 2. Extract shared wiring into helper functions

Extract common infrastructure setup (FileSystem, YamlLoader, LockFile, PromptCache, builders, etc.) into private helper functions in `cli.py`. Both `lock`, `build`, and `sync` will use these helpers.

**Rationale:** The lock command creates `FileSystem`, `YamlLoader`, `LockFile`, `PromptCache`, `LocalFileFetcher`. The build command creates `FileSystem`, `YamlLoader`, `LockFile`, `PromptCache`, builders. Sync needs all of them. Extracting shared wiring avoids triple duplication.

**Alternative considered:** A factory class or dependency injection container. Rejected as over-engineering for 3 commands with straightforward wiring.

### 3. Error handling matches existing pattern

Sync catches errors from both phases: `SyncError`, `ValidationError`, `FileNotFoundError` (from lock) and `BuildError` (from build). If lock fails, build is not attempted.

**Rationale:** Fail-fast is the project's error handling strategy. If lock fails, the lock file may be inconsistent, so building would produce incorrect results.

## Risks / Trade-offs

- **[Risk] Lock succeeds but build fails** → User gets a valid lock file but no artifacts. Mitigation: clear error message telling user to run `promptkit build` after fixing the issue. The lock file is still valid and useful.
- **[Risk] Duplicated error types in catch blocks** → Sync must catch the union of lock + build errors. Mitigation: keep the error types explicit rather than catching broad `PromptError` base class, for clarity.
