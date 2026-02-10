## Context

Phases 1-4 established the domain model, config loading, and project scaffolding. The domain layer has `Prompt`, `PromptSpec`, `LockEntry`, and protocols (`PromptFetcher`, `FileSystem`). Infrastructure has `YamlLoader`, `LockFile` serializer, and `LocalFileSystem`. The `init` command works end-to-end.

Phase 5 adds the first data-processing command: `lock`. It must fetch prompt content (local files for now, remote fetchers later), store it in a content-addressable cache, and write a lock file recording exact hashes.

**Constraints:**
- Domain layer must not depend on infrastructure
- TDD: every component gets tests before implementation
- `ClaudeMarketplaceFetcher` is deferred to Phase 9 — the lock command accepts any `PromptFetcher` via dependency injection
- Local prompts use `local/<filename>` source format in the lock file

## Goals / Non-Goals

**Goals:**
- Implement content-addressable `PromptCache` for `.promptkit/cache/`
- Implement `LocalFileFetcher` that discovers and reads prompts from `prompts/`
- Implement `LockPrompts` use case that orchestrates fetch → cache → lock
- Wire up `promptkit lock` CLI command
- Extend `FileSystem` protocol with read operations needed by cache and fetcher

**Non-Goals:**
- Remote fetching (ClaudeMarketplaceFetcher) — Phase 9
- Build command integration — Phase 6
- Sync command composition — Phase 7
- Progress bars or rich output — Phase 10
- Frontmatter parsing for routing — directory-based routing means no parsing needed

## Decisions

### 1. Extend FileSystem protocol with `read_file` and `list_directory`

The existing `FileSystem` protocol has only write-oriented methods. Cache retrieval and local file discovery need read operations.

**Decision:** Add `read_file(path) -> str` and `list_directory(path) -> list[Path]` to the `FileSystem` protocol. Update `LocalFileSystem` to implement them.

**Alternative considered:** Create a separate `ReadableFileSystem` protocol. Rejected because it fragments a cohesive abstraction — file systems naturally support both reads and writes, and splitting them adds protocol complexity without benefit.

### 2. PromptCache uses content-addressable storage with SHA256

**Decision:** Cache files are named `sha256-<hex>.md` in `.promptkit/cache/`. The `PromptCache` adapter stores content by hash and retrieves by hash. It does not need to know about prompt names or sources — that mapping lives in the lock file.

**Interface:**
- `store(content: str) -> str` — writes content to cache, returns content hash
- `retrieve(content_hash: str) -> str | None` — reads content by hash, returns None if missing
- `has(content_hash: str) -> bool` — checks if hash exists in cache

**Alternative considered:** Name-based cache (e.g., `registry-name.md`). Rejected per technical design — content-addressable avoids naming conflicts and enables deduplication.

### 3. LocalFileFetcher scans `prompts/` directory recursively

**Decision:** `LocalFileFetcher` implements `PromptFetcher` but also provides `discover() -> list[PromptSpec]` to find all local prompts. It scans `prompts/` for `.md` files, using subdirectory as category (e.g., `prompts/skills/my-skill.md`). Each discovered file gets source `local/<relative-path-without-extension>`.

The `fetch()` method takes a `PromptSpec` with source `local/<name>`, reads the corresponding file, and returns a `Prompt`.

**Alternative considered:** Having `LockPrompts` scan the directory directly. Rejected because file discovery is infrastructure concern, not use-case logic.

### 4. LockPrompts use case handles both remote and local prompts

**Decision:** `LockPrompts` receives:
- A `dict[str, PromptFetcher]` mapping registry names to fetchers (keyed by registry name, e.g., `"claude-plugins-official"`)
- A `LocalFileFetcher` for local prompt discovery and fetching
- `FileSystem` for reading config and writing lock file
- `LockFile` for serialization

**Algorithm:**
1. Read `promptkit.yaml` → get `LoadedConfig`
2. Read existing `promptkit.lock` → get existing `list[LockEntry]` (empty if no lock file)
3. For each remote `PromptSpec`: look up fetcher by registry name, fetch, cache, create `LockEntry`
4. For each local prompt discovered by `LocalFileFetcher`: fetch, cache, create `LockEntry`
5. Preserve `fetched_at` from existing lock entries when content hash hasn't changed
6. Write updated `promptkit.lock`

**Alternative considered:** Having the use case take a single `PromptFetcher` and routing internally. Rejected because the use case shouldn't know about registry types — it delegates to the right fetcher based on the registry name from config.

### 5. Lock entries preserve timestamps when content unchanged

**Decision:** When computing new lock entries, compare each prompt's content hash against the existing lock entry (if any). If unchanged, reuse the existing `fetched_at` timestamp. If changed or new, use the current time.

This produces minimal lock file diffs — only changed prompts get new timestamps, making code review easier.

### 6. CLI `lock` command reads config from cwd

**Decision:** The `lock` CLI command reads `promptkit.yaml` from `Path.cwd()`, following the same pattern as `init`. It wires up real infrastructure: `LocalFileSystem`, `YamlLoader`, `LockFile`, `PromptCache`, `LocalFileFetcher`. For MVP, no remote fetchers are wired (the fetchers dict will be empty until Phase 9).

## Risks / Trade-offs

- **FileSystem protocol change is backward-compatible but affects test doubles** → All existing tests that create mock FileSystems will still work since they only use the existing methods. New tests will need the extended protocol.
- **No remote fetchers in this phase** → Lock command can only lock local prompts. This is by design — remote fetching is Phase 9. The architecture supports adding fetchers without changing the use case.
- **PromptSpec.prompt_name assumes source contains `/`** → Local prompts use `local/<name>` format which works with the existing `source.split("/", 1)` logic. No domain changes needed.
