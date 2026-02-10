## Why

The domain model and config loading are complete (Phases 1-4), but promptkit cannot yet fetch prompts or produce a lock file. The `lock` command is the first command that does real work — it resolves the declared prompt specs in `promptkit.yaml` into concrete, hashed content stored in a content-addressable cache and recorded in `promptkit.lock`. Without it, `build` and `sync` have nothing to work with.

## What Changes

- **New `PromptCache` adapter** — content-addressable storage in `.promptkit/cache/` keyed by SHA256 hash. Stores fetched prompt content, retrieves by hash, verifies integrity.
- **New `LocalFileFetcher` adapter** — implements `PromptFetcher` protocol to read prompts from the `prompts/` directory. Discovers all `.md` files, constructs `Prompt` aggregates with `local/<filename>` source format.
- **New `LockPrompts` use case** — orchestrates the full lock workflow: load config, load existing lock (if any), fetch each prompt (remote via registry fetcher or local via `LocalFileFetcher`), cache content, diff against existing lock entries, write updated `promptkit.lock`.
- **New `lock` CLI command** — wires up `LockPrompts` with real infrastructure and exposes it as `promptkit lock`.
- **Extend `FileSystem` protocol** — add `read_file` and `list_directory` methods needed by the cache and local fetcher (currently only has write/exists/create/append).

## Capabilities

### New Capabilities
- `prompt-cache`: Content-addressable storage for fetched prompt files (`.promptkit/cache/sha256-<hash>.md`)
- `local-file-fetcher`: Fetching prompts from the local `prompts/` directory as a `PromptFetcher` implementation
- `lock-prompts`: The `LockPrompts` use case that orchestrates fetch → cache → lock for all declared and local prompts
- `cli-lock-command`: The `promptkit lock` CLI command that wires up the use case

### Modified Capabilities
- `project-scaffold`: `FileSystem` protocol gains `read_file` and `list_directory` methods required by cache and fetcher

## Impact

- **Domain layer** — `FileSystem` protocol extended with read operations (minor, backward-compatible addition)
- **Infrastructure layer** — two new adapters (`PromptCache` in `infra/storage/`, `LocalFileFetcher` in `infra/fetchers/`), `LocalFileSystem` updated to implement new protocol methods
- **Application layer** — new `LockPrompts` use case in `app/lock.py`
- **CLI** — new `lock` command in `cli.py`
- **Dependencies** — no new runtime dependencies (uses existing `pyyaml`, `pathlib`, `hashlib`)
- **Remote fetchers** — `ClaudeMarketplaceFetcher` is NOT included in this phase (stubbed/deferred to Phase 9). Lock command will work with local prompts and any fetcher passed in.
