## Why

`promptkit sync` fails with `"No fetcher registered for registry: claude-plugins-official"` because `cli.py` passes `fetchers={}` to the lock use case. No remote fetcher exists — only `LocalFileFetcher`. Both Claude marketplace registries (`anthropics/claude-plugins-official` and `anthropics/skills`) use the same `marketplace.json` manifest pattern and need a single fetcher implementation.

## What Changes

- **New `Plugin` domain value object** — a manifest representing a fetched plugin: spec + commit SHA + file list. No content loaded into memory; files stay on disk in cache.
- **New `PluginFetcher` protocol** — replaces `PromptFetcher` for remote plugins. `fetch(spec) → Plugin`. Downloads the entire plugin directory (agents, commands, skills, hooks, scripts, configs — everything) to a cache directory keyed by `{registry}/{plugin}/{commit_sha}/`.
- **New `ClaudeMarketplaceFetcher`** — implements `PluginFetcher`. Reads `marketplace.json` via GitHub Contents API, discovers all files in the plugin directory, downloads them to cache. Returns a `Plugin` manifest.
- **New `PluginCache`** — directory-based cache keyed by `{registry}/{plugin}/{commit_sha}/`. Replaces content-addressable `PromptCache` for remote plugins. Stores the full plugin directory tree on disk.
- **`LockEntry` gains `commit_sha` field** — for remote plugins, the lock file records the commit SHA instead of (or alongside) content hash. Local prompts keep content hash.
- **`LockPrompts` use case** updated — calls `PluginFetcher.fetch(spec)` for remote specs, gets back a `Plugin` manifest, writes one lock entry per plugin (not per file).
- **`BuildArtifacts` use case** updated — for remote plugins, reads files directly from `PluginCache` directory and copies to platform output dirs. Builders handle directory structure mapping (e.g., `skills/` → `skills-cursor/` for Cursor).
- **`ArtifactBuilder` protocol** updated — builders receive both `list[Prompt]` (local) and cached plugin directories (remote) and copy/transform as needed.
- **CLI wiring** — `_make_lock_use_case` reads registries from config and maps `CLAUDE_MARKETPLACE` type to `ClaudeMarketplaceFetcher(registry.url)`.

## Marketplace Structure (reference)

See `docs/references/claude-marketplace-spec.md` for full upstream spec.

**Key patterns:**
- **Plugins repo** (`claude-plugins-official`): `source: "./plugins/<name>"`, plugins contain `agents/`, `commands/`, `skills/`, `hooks/`, `.mcp.json`, scripts, etc.
- **Skills repo** (`anthropic-agent-skills`): `source: "./"`, plugins list skills explicitly via `skills` array, each skill dir has `SKILL.md` + optional scripts.
- **External plugins**: `source: {source: "url", url: "https://...git"}` — **skipped for MVP**, only relative-path sources handled.

## Capabilities

### New Capabilities
- `plugin-fetcher`: Domain protocol for fetching entire plugin directories from registries
- `claude-marketplace-fetcher`: GitHub-based implementation that downloads full plugin directories to cache
- `plugin-cache`: Directory-based cache for plugin contents, keyed by commit SHA
- `plugin-domain-model`: `Plugin` value object representing a fetched plugin manifest

### Modified Capabilities
- `lock-prompts`: Writes one lock entry per plugin with commit SHA; local prompts unchanged
- `build-artifacts`: Reads from plugin cache directory and copies files to platform output
- `lock-entry`: Gains `commit_sha` field for remote plugins

### Unchanged
- `local-file-fetcher`: Still works with `Prompt` objects for local `prompts/` directory
- `prompt`: Still used for local prompts (content in memory)

## Impact

- **Domain layer**: New `Plugin` value object, new `PluginFetcher` protocol, `LockEntry` gains `commit_sha`
- **Infrastructure layer**: New `ClaudeMarketplaceFetcher`, new `PluginCache`; builders updated to copy from cache
- **Application layer**: `LockPrompts` and `BuildArtifacts` updated for dual model (local Prompt + remote Plugin)
- **CLI layer**: `_make_lock_use_case()` wires fetchers from config registries
- **Dependencies**: `httpx` already in `pyproject.toml`
- **Tests**: All existing tests need updating for new protocol signatures; new tests for Plugin, PluginFetcher, ClaudeMarketplaceFetcher, PluginCache

## Decisions Made

1. **Sync entire plugin directory** — not just `.md` files. Hooks, scripts, MCP configs, LSP configs all get cached.
2. **Plugin as manifest** — `Plugin` holds file paths, not content. Files stay on disk in cache.
3. **Builders just copy** — no transformation of non-md files. Directory structure mapping only (e.g., `skills/` → `skills-cursor/`).
4. **Skip external git URL sources for MVP** — only handle relative-path plugins within the registry repo.
5. **Cache by commit SHA** — `{registry}/{plugin}/{commit_sha}/` directory structure. Lock file records SHA for reproducibility.
