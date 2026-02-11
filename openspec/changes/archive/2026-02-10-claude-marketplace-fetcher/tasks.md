## 1. Add Plugin domain value object

- [x] 1.1 Create `source/promptkit/domain/plugin.py` with frozen `Plugin` dataclass: `spec: PromptSpec`, `files: tuple[str, ...]`, `source_dir: Path`, `commit_sha: str | None = None`
- [x] 1.2 Write tests in `tests/domain/test_plugin.py`: construction, frozen, properties, local vs registry variants
- [x] 1.3 Run `pytest tests/domain/test_plugin.py -v` — green

## 2. Add PluginFetcher protocol, remove PromptFetcher

- [x] 2.1 Add `PluginFetcher` protocol to `source/promptkit/domain/protocols.py`: `fetch(spec) -> Plugin` (cache_dir injected at construction, not per-call)
- [x] 2.2 Remove `PromptFetcher` protocol entirely from `protocols.py`
- [x] 2.3 Remove `Prompt` import from `protocols.py` (no longer needed)
- [x] 2.4 Run `pyright` — identify all downstream breakages from removing `PromptFetcher` and `Prompt`

## 3. Add commit_sha to LockEntry

- [x] 3.1 Add `commit_sha: str | None = None` field to `LockEntry` in `source/promptkit/domain/lock_entry.py` (keep `content_hash: str` — use `""` for registry plugins)
- [x] 3.2 Update `LockFile.serialize()` / `LockFile.deserialize()` in `source/promptkit/infra/config/lock_file.py` to handle `commit_sha` (write when present, parse when present, default to None)
- [x] 3.3 Update `tests/domain/test_lock_entry.py` for new field
- [x] 3.4 Update `tests/infra/config/test_lock_file.py` for serialization/deserialization with and without commit_sha
- [x] 3.5 Run `pytest tests/domain/test_lock_entry.py tests/infra/config/test_lock_file.py -v` — green

## 4. Implement PluginCache

- [x] 4.1 Create `source/promptkit/infra/storage/plugin_cache.py` with `PluginCache` class
- [x] 4.2 Implement `has(registry, plugin, sha) -> bool` — check if cache dir exists
- [x] 4.3 Implement `plugin_dir(registry, plugin, sha) -> Path` — return cache path
- [x] 4.4 Implement `list_files(registry, plugin, sha) -> list[str]` — list relative paths in cached dir
- [x] 4.5 Write tests in `tests/infra/storage/test_plugin_cache.py`
- [x] 4.6 Run `pytest tests/infra/storage/test_plugin_cache.py -v` — green

## 5. Update LocalFileFetcher → LocalPluginFetcher

- [x] 5.1 Rename `source/promptkit/infra/fetchers/local_file_fetcher.py` → `local_plugin_fetcher.py`
- [x] 5.2 Rename class `LocalFileFetcher` → `LocalPluginFetcher`
- [x] 5.3 Update `discover()`: scan for both single `.md` files AND directories (non-.md files too)
- [x] 5.4 Update `fetch(spec) -> Plugin`: return `Plugin(spec, files, source_dir=prompts_dir)` instead of `Prompt`
- [x] 5.5 Handle single-file plugins: `prompts/my-rule.md` → `Plugin(files=("my-rule.md",))`
- [x] 5.6 Handle directory plugins: `prompts/my-skill/` → `Plugin(files=("my-skill/SKILL.md", "my-skill/scripts/check.sh"))`
- [x] 5.7 Update all imports across codebase (`LocalFileFetcher` → `LocalPluginFetcher`)
- [x] 5.8 Update tests in `tests/infra/fetchers/test_local_file_fetcher.py` → `test_local_plugin_fetcher.py`
- [x] 5.9 Add tests: discover directory plugins, fetch directory plugins, fetch single-file plugins returning Plugin
- [x] 5.10 Run `pytest tests/infra/fetchers/test_local_plugin_fetcher.py -v` — green

## 6. Implement ClaudeMarketplaceFetcher

- [x] 6.1 Create `source/promptkit/infra/fetchers/claude_marketplace.py` with `ClaudeMarketplaceFetcher` class
- [x] 6.2 Implement URL parsing: extract `owner`/`repo` from `https://github.com/{owner}/{repo}`, raise `SyncError` for invalid URLs
- [x] 6.3 Implement `_fetch_marketplace_json()`: GET `.claude-plugin/marketplace.json` via Contents API, parse JSON, find plugin entry by name
- [x] 6.4 Implement `_get_latest_commit_sha()`: GET repo's default branch latest commit SHA via GitHub API
- [x] 6.5 Implement `_resolve_source_path()`: handle string sources (strip `./` prefix) and reject object sources (external git URLs) with SyncError
- [x] 6.6 Implement `_list_directory_recursive()`: list all files in plugin directory tree via Contents API
- [x] 6.7 Implement `_handle_skills_array()`: when plugin entry has `skills` array, list files in each skill directory
- [x] 6.8 Implement `_download_files()`: download each file via `download_url` and write to cache directory
- [x] 6.9 Implement `fetch(spec) -> Plugin`: orchestrate marketplace lookup → SHA check → directory listing → download → Plugin construction (cache_dir injected at construction)

## 7. Write unit tests for ClaudeMarketplaceFetcher

- [x] 7.1 Create `tests/infra/fetchers/test_claude_marketplace.py` with mocked `httpx.Client`
- [x] 7.2 Test: plugin found with relative path source, all files downloaded
- [x] 7.3 Test: multi-file plugin (agents + commands + hooks + scripts)
- [x] 7.4 Test: skills repo structure (plugin with `skills` array)
- [x] 7.5 Test: external git URL source → SyncError
- [x] 7.6 Test: plugin not found in marketplace.json → SyncError
- [x] 7.7 Test: network/HTTP failure → SyncError
- [x] 7.8 Test: GitHub URL parsing (valid and invalid)
- [x] 7.9 Test: commit SHA retrieval
- [x] 7.10 Run `pytest tests/infra/fetchers/test_claude_marketplace.py -v` — green

## 8. Update LockPrompts use case (single code path)

- [x] 8.1 Replace `fetchers: Mapping[str, PromptFetcher]` + `local_fetcher: LocalFileFetcher` with `local_fetcher: LocalPluginFetcher` + `fetchers: Mapping[str, PluginFetcher]` (separate local fetcher for discover() support)
- [x] 8.2 Remove `_lock_prompt()` method (was `Prompt`-based), replace with `_lock_plugin()` creating LockEntry from Plugin
- [x] 8.3 Single loop: for each spec, resolve fetcher by registry name, call `fetcher.fetch(spec)`, create LockEntry
- [x] 8.4 For local plugins: compute content_hash in LockPrompts by reading files from plugin.source_dir via FileSystem (not in Plugin domain object), commit_sha=None
- [x] 8.5 For registry plugins: content_hash="", commit_sha from Plugin
- [x] 8.6 SHA-based skip logic: if existing lock entry has same commit_sha, preserve timestamp
- [x] 8.7 Remove `PromptCache` dependency — no longer needed
- [x] 8.8 Update `tests/app/test_lock.py` with `FakePluginFetcher` returning `Plugin` objects
- [x] 8.9 Add tests: lock local single-file, lock local directory, lock registry plugin, SHA skip logic
- [x] 8.10 Run `pytest tests/app/test_lock.py -v` — green

## 9. Update BuildArtifacts use case (single code path)

- [x] 9.1 Remove `PromptCache` dependency
- [x] 9.2 Add `PluginCache` dependency for resolving registry plugin source dirs
- [x] 9.3 Replace `_load_prompt()` with `_resolve_source_dir()`: local → `prompts/`, registry → `PluginCache` dir
- [x] 9.4 Update builder calls: pass `list[Plugin]` instead of `list[Prompt]`
- [x] 9.5 Update `tests/app/test_build.py` for new Plugin-based build path
- [x] 9.6 Add tests: build local single-file, build local directory, build registry plugin, cache missing → BuildError
- [x] 9.7 Run `pytest tests/app/test_build.py -v` — green

## 10. Update ArtifactBuilder protocol and builders

- [x] 10.1 Update `ArtifactBuilder` protocol: `build(plugins: list[Plugin], output_dir)` instead of `build(prompts: list[Prompt], output_dir)`
- [x] 10.2 Update `CursorBuilder`: copy file tree from source_dir to output_dir with directory mapping, skip unsupported categories (agents, commands, hooks)
- [x] 10.3 Update `ClaudeBuilder`: copy file tree from source_dir to output_dir preserving structure
- [x] 10.4 Handle non-md files: copy as-is (no extension filtering)
- [x] 10.5 Update `tests/infra/builders/test_cursor_builder.py` and `test_claude_builder.py`
- [x] 10.6 Add tests: multi-file plugin build, non-md file copy, directory mapping, category filtering for Cursor
- [x] 10.7 Run `pytest tests/infra/builders/ -v` — green

## 11. Remove Prompt, PromptFetcher, PromptCache

- [x] 11.1 Delete `source/promptkit/domain/prompt.py` (or keep as deprecated if needed for migration)
- [x] 11.2 Delete `source/promptkit/domain/prompt_metadata.py` (no longer used)
- [x] 11.3 Delete `source/promptkit/infra/storage/prompt_cache.py`
- [x] 11.4 Remove all `Prompt`/`PromptFetcher`/`PromptCache` imports across codebase
- [x] 11.5 Update/delete `tests/domain/test_prompt.py`, `tests/domain/test_prompt_metadata.py`, `tests/infra/storage/test_prompt_cache.py`
- [x] 11.6 Run `pytest -x` — green (no broken imports, no references to removed code)

## 12. Wire fetchers in CLI

- [x] 12.1 Add `_make_plugin_fetchers(registries)` helper in `source/promptkit/cli.py` mapping `CLAUDE_MARKETPLACE` registries to `ClaudeMarketplaceFetcher`
- [x] 12.2 Always include `"local"` key → `LocalPluginFetcher` in the fetcher map
- [x] 12.3 Update `_make_lock_use_case()` to pass unified `plugin_fetchers` mapping
- [x] 12.4 Update `_make_build_use_case()` to include `PluginCache`

## 13. Update integration tests

- [x] 13.1 Replace `GitHubRegistryFetcher` prototype in `tests/integration/test_lock_with_real_registry.py` with real `ClaudeMarketplaceFetcher`
- [x] 13.2 Update integration test to verify plugin directory is cached (not just single .md file)
- [x] 13.3 Add integration test: sync a plugin with multiple file types (agents, hooks, scripts)
- [x] 13.4 Update e2e tests for new lock entry format (commit_sha)

## 14. Verification

- [x] 14.1 Run `pytest -x` — all existing + new tests pass
- [x] 14.2 Run `pyright` — no type errors
- [x] 14.3 Run `ruff check .` — no lint issues
- [x] 14.4 Run `ruff format --check .` — properly formatted
