## Why

`promptkit sync` fails with `"No fetcher registered for registry: claude-plugins-official"` because `cli.py` passes `fetchers={}` to the lock use case. No remote fetcher exists — only `LocalFileFetcher`. Both Claude marketplace registries (`anthropics/claude-plugins-official` and `anthropics/skills`) use the same `marketplace.json` manifest pattern and need a single fetcher implementation.

Additionally, the current model assumes all prompts are single `.md` files with content loaded into memory (`Prompt` aggregate). This doesn't fit reality — both registry plugins AND local prompts can be multi-file directories containing `.md`, `.json`, scripts, hooks, and configs. The model must be unified around file trees on disk.

## What Changes

- **Unified `Plugin` domain value object** — replaces `Prompt` as the core model. A manifest representing a fetched plugin: spec + file list + optional commit SHA. Files stay on disk (in cache or in `prompts/`), never loaded into memory. Works for both local and registry plugins.
- **Remove `Prompt` aggregate** — no longer needed. Everything is a `Plugin` (a file tree on disk).
- **Remove `PromptFetcher` protocol** — replaced by `PluginFetcher` for both local and registry.
- **Remove `PromptCache`** (content-addressable) — replaced by `PluginCache` (directory-based) for registry plugins. Local plugins read from `prompts/` directly.
- **New `PluginFetcher` protocol** — `fetch(spec, cache_dir) → Plugin`. Both `LocalPluginFetcher` and `ClaudeMarketplaceFetcher` implement this.
- **`LocalFileFetcher` → `LocalPluginFetcher`** — updated to handle directories + non-md files. Scans `prompts/`, returns `Plugin` manifests with file lists.
- **New `ClaudeMarketplaceFetcher`** — implements `PluginFetcher`. Reads `marketplace.json` via GitHub Contents API, discovers all files in the plugin directory, downloads them to cache. Returns a `Plugin` manifest.
- **New `PluginCache`** — directory-based cache keyed by `{registry}/{plugin}/{commit_sha}/`. Stores the full plugin directory tree on disk.
- **`LockEntry` gains `commit_sha` field** — for registry plugins, the lock file records the commit SHA. Local plugins keep content hash. `content_hash = ""` for registry plugins.
- **`LockPrompts` use case** — single code path. Calls `PluginFetcher.fetch()` for every spec (local or registry), writes one lock entry per plugin.
- **`BuildArtifacts` use case** — single code path. Resolves source directory for each lock entry, copies file tree to platform output.
- **`ArtifactBuilder` protocol** updated — builders receive source directories + file lists, copy files to platform output with directory mapping.
- **CLI wiring** — maps registries to `ClaudeMarketplaceFetcher`, local to `LocalPluginFetcher`.

## Marketplace Structure (reference)

See `docs/references/claude-marketplace-spec.md` for full upstream spec.

**Key patterns:**
- **Plugins repo** (`claude-plugins-official`): `source: "./plugins/<name>"`, plugins contain `agents/`, `commands/`, `skills/`, `hooks/`, `.mcp.json`, scripts, etc.
- **Skills repo** (`anthropic-agent-skills`): `source: "./"`, plugins list skills explicitly via `skills` array, each skill dir has `SKILL.md` + optional scripts.
- **External plugins**: `source: {source: "url", url: "https://...git"}` — **skipped for MVP**, only relative-path sources handled.

## Capabilities

### New Capabilities
- `plugin-domain-model`: Unified `Plugin` value object for both local and registry
- `plugin-fetcher`: Domain protocol for fetching plugin directories (local or remote)
- `claude-marketplace-fetcher`: GitHub-based implementation that downloads full plugin directories to cache
- `plugin-cache`: Directory-based cache for registry plugin contents, keyed by commit SHA

### Modified Capabilities
- `lock-prompts`: Single code path — all specs produce `Plugin` manifests and `LockEntry`s
- `build-artifacts`: Single code path — resolves source dir, copies file tree to platform output
- `lock-entry`: Gains `commit_sha` field for registry plugins
- `local-file-fetcher`: Renamed to `LocalPluginFetcher`, handles directories + non-md files

### Removed
- `prompt`: `Prompt` aggregate removed — replaced by `Plugin`
- `prompt-fetcher`: `PromptFetcher` protocol removed — replaced by `PluginFetcher`
- `prompt-cache`: `PromptCache` removed — registry uses `PluginCache`, local reads from `prompts/` directly

## Impact

- **Domain layer**: `Plugin` replaces `Prompt`, `PluginFetcher` replaces `PromptFetcher`, `LockEntry` gains `commit_sha`
- **Infrastructure layer**: New `ClaudeMarketplaceFetcher`, new `PluginCache`; `LocalFileFetcher` → `LocalPluginFetcher`; builders updated to copy file trees; `PromptCache` removed
- **Application layer**: `LockPrompts` and `BuildArtifacts` simplified to single code path
- **CLI layer**: `_make_lock_use_case()` wires both local and registry fetchers
- **Dependencies**: `httpx` already in `pyproject.toml`
- **Tests**: Significant updates — `Prompt`-based tests migrate to `Plugin`-based, new tests for all new components

## Decisions Made

1. **Unified model** — both local and registry plugins are `Plugin` (file tree on disk). No dual model.
2. **Plugin as manifest** — `Plugin` holds file paths, not content. Files stay on disk.
3. **Local prompts can be multi-file** — a directory in `prompts/` with `.md`, `.json`, scripts, etc. is a valid local plugin.
4. **Builders just copy** — copy files from source to output. No hard links, no symlinks, no content transformation. Directory mapping only (e.g., `skills/` → `skills-cursor/` for Cursor).
5. **Skip external git URL sources for MVP** — only handle relative-path plugins within the registry repo.
6. **Cache by commit SHA** — registry plugins use `{registry}/{plugin}/{commit_sha}/` directory structure. Lock file records SHA for reproducibility.
7. **`content_hash = ""`** for registry plugins — no type change to optional. `commit_sha` is the discriminator.
