## 1. Add Plugin domain value object

- [ ] 1.1 Create `source/promptkit/domain/plugin.py` with frozen `Plugin` dataclass: `spec: PromptSpec`, `commit_sha: str`, `files: tuple[str, ...]`
- [ ] 1.2 Write tests in `tests/domain/test_plugin.py`: construction, frozen, properties
- [ ] 1.3 Run `pytest tests/domain/test_plugin.py -v` — green

## 2. Add PluginFetcher protocol

- [ ] 2.1 Add `PluginFetcher` protocol to `source/promptkit/domain/protocols.py`: `fetch(spec, cache_dir) -> Plugin`
- [ ] 2.2 Revert `PromptFetcher.fetch()` return type back to `Prompt` (undo the `list[Prompt]` change — no longer needed)
- [ ] 2.3 Run `pyright` — no type errors

## 3. Add commit_sha to LockEntry

- [ ] 3.1 Add `commit_sha: str | None = None` field to `LockEntry` in `source/promptkit/domain/lock_entry.py`
- [ ] 3.2 Update `LockFile.serialize()` / `LockFile.deserialize()` in `source/promptkit/infra/config/lock_file.py` to handle `commit_sha` (write when present, parse when present, default to None)
- [ ] 3.3 Update `tests/domain/test_lock_entry.py` for new field
- [ ] 3.4 Update `tests/infra/config/test_lock_file.py` for serialization/deserialization with and without commit_sha
- [ ] 3.5 Run `pytest tests/domain/test_lock_entry.py tests/infra/config/test_lock_file.py -v` — green

## 4. Implement PluginCache

- [ ] 4.1 Create `source/promptkit/infra/storage/plugin_cache.py` with `PluginCache` class
- [ ] 4.2 Implement `has(registry, plugin, sha) -> bool` — check if cache dir exists
- [ ] 4.3 Implement `plugin_dir(registry, plugin, sha) -> Path` — return cache path
- [ ] 4.4 Implement `list_files(registry, plugin, sha) -> list[str]` — list relative paths in cached dir
- [ ] 4.5 Write tests in `tests/infra/storage/test_plugin_cache.py`
- [ ] 4.6 Run `pytest tests/infra/storage/test_plugin_cache.py -v` — green

## 5. Implement ClaudeMarketplaceFetcher

- [ ] 5.1 Create `source/promptkit/infra/fetchers/claude_marketplace.py` with `ClaudeMarketplaceFetcher` class
- [ ] 5.2 Implement URL parsing: extract `owner`/`repo` from `https://github.com/{owner}/{repo}`, raise `SyncError` for invalid URLs
- [ ] 5.3 Implement `_fetch_marketplace_json()`: GET `.claude-plugin/marketplace.json` via Contents API, parse JSON, find plugin entry by name
- [ ] 5.4 Implement `_get_latest_commit_sha()`: GET repo's default branch latest commit SHA via GitHub API
- [ ] 5.5 Implement `_resolve_source_path()`: handle string sources (strip `./` prefix) and reject object sources (external git URLs) with SyncError
- [ ] 5.6 Implement `_list_directory_recursive()`: list all files in plugin directory tree via Contents API
- [ ] 5.7 Implement `_handle_skills_array()`: when plugin entry has `skills` array, list files in each skill directory
- [ ] 5.8 Implement `_download_files()`: download each file via `download_url` and write to cache directory
- [ ] 5.9 Implement `fetch(spec, cache_dir) -> Plugin`: orchestrate marketplace lookup → SHA check → directory listing → download → Plugin construction

## 6. Write unit tests for ClaudeMarketplaceFetcher

- [ ] 6.1 Create `tests/infra/fetchers/test_claude_marketplace.py` with mocked `httpx.Client`
- [ ] 6.2 Test: plugin found with relative path source, all files downloaded
- [ ] 6.3 Test: multi-file plugin (agents + commands + hooks + scripts)
- [ ] 6.4 Test: skills repo structure (plugin with `skills` array)
- [ ] 6.5 Test: external git URL source → SyncError
- [ ] 6.6 Test: plugin not found in marketplace.json → SyncError
- [ ] 6.7 Test: network/HTTP failure → SyncError
- [ ] 6.8 Test: GitHub URL parsing (valid and invalid)
- [ ] 6.9 Test: commit SHA retrieval
- [ ] 6.10 Run `pytest tests/infra/fetchers/test_claude_marketplace.py -v` — green

## 7. Update LockPrompts use case

- [ ] 7.1 Add `plugin_fetchers: Mapping[str, PluginFetcher]` parameter to `LockPrompts.__init__()` (alongside existing `fetchers` for local)
- [ ] 7.2 Update remote prompt loop: call `plugin_fetcher.fetch(spec, cache_dir)` → get `Plugin` → create one `LockEntry` with `commit_sha`
- [ ] 7.3 Implement SHA-based skip logic: if existing lock entry has same `commit_sha`, preserve timestamp
- [ ] 7.4 Update `tests/app/test_lock.py` with `FakePluginFetcher` returning `Plugin` objects
- [ ] 7.5 Add test: remote plugin creates lock entry with commit_sha
- [ ] 7.6 Add test: same commit_sha preserves timestamp (skip re-download)
- [ ] 7.7 Add test: changed commit_sha updates timestamp
- [ ] 7.8 Run `pytest tests/app/test_lock.py -v` — green

## 8. Update BuildArtifacts use case

- [ ] 8.1 Add `plugin_cache: PluginCache` parameter to `BuildArtifacts.__init__()`
- [ ] 8.2 Update `_load_prompt()`: for entries with `commit_sha`, resolve cache dir and read files from disk instead of from `PromptCache`
- [ ] 8.3 Update builders to handle plugin directories: walk cache dir, copy files to output with directory mapping (skills/ → skills-cursor/ for Cursor)
- [ ] 8.4 Update `tests/app/test_build.py` for remote plugin build path
- [ ] 8.5 Run `pytest tests/app/test_build.py -v` — green

## 9. Wire fetchers in CLI

- [ ] 9.1 Add `_make_plugin_fetchers(registries)` helper in `source/promptkit/cli.py` mapping `CLAUDE_MARKETPLACE` registries to `ClaudeMarketplaceFetcher`
- [ ] 9.2 Update `_make_lock_use_case()` to load config, extract registries, and pass plugin_fetchers
- [ ] 9.3 Update `_make_build_use_case()` to include `PluginCache`

## 10. Update integration tests

- [ ] 10.1 Replace `GitHubRegistryFetcher` prototype in `tests/integration/test_lock_with_real_registry.py` with real `ClaudeMarketplaceFetcher`
- [ ] 10.2 Update integration test to verify plugin directory is cached (not just single .md file)
- [ ] 10.3 Add integration test: sync a plugin with multiple file types (agents, hooks, scripts)
- [ ] 10.4 Update e2e tests for new lock entry format (commit_sha)

## 11. Verification

- [ ] 11.1 Run `pytest -x` — all existing + new tests pass
- [ ] 11.2 Run `pyright` — no type errors
- [ ] 11.3 Run `ruff check .` — no lint issues
- [ ] 11.4 Run `ruff format --check .` — properly formatted
