## 1. Add Plugin domain value object

- [ ] 1.1 Create `source/promptkit/domain/plugin.py` with frozen `Plugin` dataclass: `spec: PromptSpec`, `files: tuple[str, ...]`, `source_dir: Path`, `commit_sha: str | None = None`
- [ ] 1.2 Write tests in `tests/domain/test_plugin.py`: construction, frozen, properties, local vs registry variants
- [ ] 1.3 Run `pytest tests/domain/test_plugin.py -v` — green

## 2. Add PluginFetcher protocol, remove PromptFetcher

- [ ] 2.1 Add `PluginFetcher` protocol to `source/promptkit/domain/protocols.py`: `fetch(spec) -> Plugin` (cache_dir injected at construction, not per-call)
- [ ] 2.2 Remove `PromptFetcher` protocol entirely from `protocols.py`
- [ ] 2.3 Remove `Prompt` import from `protocols.py` (no longer needed)
- [ ] 2.4 Run `pyright` — identify all downstream breakages from removing `PromptFetcher` and `Prompt`

## 3. Add commit_sha to LockEntry

- [ ] 3.1 Add `commit_sha: str | None = None` field to `LockEntry` in `source/promptkit/domain/lock_entry.py` (keep `content_hash: str` — use `""` for registry plugins)
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

## 5. Update LocalFileFetcher → LocalPluginFetcher

- [ ] 5.1 Rename `source/promptkit/infra/fetchers/local_file_fetcher.py` → `local_plugin_fetcher.py`
- [ ] 5.2 Rename class `LocalFileFetcher` → `LocalPluginFetcher`
- [ ] 5.3 Update `discover()`: scan for both single `.md` files AND directories (non-.md files too)
- [ ] 5.4 Update `fetch(spec) -> Plugin`: return `Plugin(spec, files, source_dir=prompts_dir)` instead of `Prompt`
- [ ] 5.5 Handle single-file plugins: `prompts/my-rule.md` → `Plugin(files=("my-rule.md",))`
- [ ] 5.6 Handle directory plugins: `prompts/my-skill/` → `Plugin(files=("my-skill/SKILL.md", "my-skill/scripts/check.sh"))`
- [ ] 5.7 Update all imports across codebase (`LocalFileFetcher` → `LocalPluginFetcher`)
- [ ] 5.8 Update tests in `tests/infra/fetchers/test_local_file_fetcher.py` → `test_local_plugin_fetcher.py`
- [ ] 5.9 Add tests: discover directory plugins, fetch directory plugins, fetch single-file plugins returning Plugin
- [ ] 5.10 Run `pytest tests/infra/fetchers/test_local_plugin_fetcher.py -v` — green

## 6. Implement ClaudeMarketplaceFetcher

- [ ] 6.1 Create `source/promptkit/infra/fetchers/claude_marketplace.py` with `ClaudeMarketplaceFetcher` class
- [ ] 6.2 Implement URL parsing: extract `owner`/`repo` from `https://github.com/{owner}/{repo}`, raise `SyncError` for invalid URLs
- [ ] 6.3 Implement `_fetch_marketplace_json()`: GET `.claude-plugin/marketplace.json` via Contents API, parse JSON, find plugin entry by name
- [ ] 6.4 Implement `_get_latest_commit_sha()`: GET repo's default branch latest commit SHA via GitHub API
- [ ] 6.5 Implement `_resolve_source_path()`: handle string sources (strip `./` prefix) and reject object sources (external git URLs) with SyncError
- [ ] 6.6 Implement `_list_directory_recursive()`: list all files in plugin directory tree via Contents API
- [ ] 6.7 Implement `_handle_skills_array()`: when plugin entry has `skills` array, list files in each skill directory
- [ ] 6.8 Implement `_download_files()`: download each file via `download_url` and write to cache directory
- [ ] 6.9 Implement `fetch(spec) -> Plugin`: orchestrate marketplace lookup → SHA check → directory listing → download → Plugin construction (cache_dir injected at construction)

## 7. Write unit tests for ClaudeMarketplaceFetcher

- [ ] 7.1 Create `tests/infra/fetchers/test_claude_marketplace.py` with mocked `httpx.Client`
- [ ] 7.2 Test: plugin found with relative path source, all files downloaded
- [ ] 7.3 Test: multi-file plugin (agents + commands + hooks + scripts)
- [ ] 7.4 Test: skills repo structure (plugin with `skills` array)
- [ ] 7.5 Test: external git URL source → SyncError
- [ ] 7.6 Test: plugin not found in marketplace.json → SyncError
- [ ] 7.7 Test: network/HTTP failure → SyncError
- [ ] 7.8 Test: GitHub URL parsing (valid and invalid)
- [ ] 7.9 Test: commit SHA retrieval
- [ ] 7.10 Run `pytest tests/infra/fetchers/test_claude_marketplace.py -v` — green

## 8. Update LockPrompts use case (single code path)

- [ ] 8.1 Replace `fetchers: Mapping[str, PromptFetcher]` + `local_fetcher: LocalFileFetcher` with unified `plugin_fetchers: Mapping[str, PluginFetcher]` (includes `"local"` key)
- [ ] 8.2 Remove `_lock_prompt()` method (was `Prompt`-based), replace with `_lock_plugin()` creating LockEntry from Plugin
- [ ] 8.3 Single loop: for each spec, resolve fetcher by registry name, call `fetcher.fetch(spec)`, create LockEntry
- [ ] 8.4 For local plugins: compute content_hash in LockPrompts by reading files from plugin.source_dir via FileSystem (not in Plugin domain object), commit_sha=None
- [ ] 8.5 For registry plugins: content_hash="", commit_sha from Plugin
- [ ] 8.6 SHA-based skip logic: if existing lock entry has same commit_sha, preserve timestamp
- [ ] 8.7 Remove `PromptCache` dependency — no longer needed
- [ ] 8.8 Update `tests/app/test_lock.py` with `FakePluginFetcher` returning `Plugin` objects
- [ ] 8.9 Add tests: lock local single-file, lock local directory, lock registry plugin, SHA skip logic
- [ ] 8.10 Run `pytest tests/app/test_lock.py -v` — green

## 9. Update BuildArtifacts use case (single code path)

- [ ] 9.1 Remove `PromptCache` dependency
- [ ] 9.2 Add `PluginCache` dependency for resolving registry plugin source dirs
- [ ] 9.3 Replace `_load_prompt()` with `_resolve_source_dir()`: local → `prompts/`, registry → `PluginCache` dir
- [ ] 9.4 Update builder calls: pass `list[Plugin]` instead of `list[Prompt]`
- [ ] 9.5 Update `tests/app/test_build.py` for new Plugin-based build path
- [ ] 9.6 Add tests: build local single-file, build local directory, build registry plugin, cache missing → BuildError
- [ ] 9.7 Run `pytest tests/app/test_build.py -v` — green

## 10. Update ArtifactBuilder protocol and builders

- [ ] 10.1 Update `ArtifactBuilder` protocol: `build(plugins: list[Plugin], output_dir)` instead of `build(prompts: list[Prompt], output_dir)`
- [ ] 10.2 Update `CursorBuilder`: copy file tree from source_dir to output_dir with directory mapping, skip unsupported categories (agents, commands, hooks)
- [ ] 10.3 Update `ClaudeBuilder`: copy file tree from source_dir to output_dir preserving structure
- [ ] 10.4 Handle non-md files: copy as-is (no extension filtering)
- [ ] 10.5 Update `tests/infra/builders/test_cursor_builder.py` and `test_claude_builder.py`
- [ ] 10.6 Add tests: multi-file plugin build, non-md file copy, directory mapping, category filtering for Cursor
- [ ] 10.7 Run `pytest tests/infra/builders/ -v` — green

## 11. Remove Prompt, PromptFetcher, PromptCache

- [ ] 11.1 Delete `source/promptkit/domain/prompt.py` (or keep as deprecated if needed for migration)
- [ ] 11.2 Delete `source/promptkit/domain/prompt_metadata.py` (no longer used)
- [ ] 11.3 Delete `source/promptkit/infra/storage/prompt_cache.py`
- [ ] 11.4 Remove all `Prompt`/`PromptFetcher`/`PromptCache` imports across codebase
- [ ] 11.5 Update/delete `tests/domain/test_prompt.py`, `tests/domain/test_prompt_metadata.py`, `tests/infra/storage/test_prompt_cache.py`
- [ ] 11.6 Run `pytest -x` — green (no broken imports, no references to removed code)

## 12. Wire fetchers in CLI

- [ ] 12.1 Add `_make_plugin_fetchers(registries)` helper in `source/promptkit/cli.py` mapping `CLAUDE_MARKETPLACE` registries to `ClaudeMarketplaceFetcher`
- [ ] 12.2 Always include `"local"` key → `LocalPluginFetcher` in the fetcher map
- [ ] 12.3 Update `_make_lock_use_case()` to pass unified `plugin_fetchers` mapping
- [ ] 12.4 Update `_make_build_use_case()` to include `PluginCache`

## 13. Update integration tests

- [ ] 13.1 Replace `GitHubRegistryFetcher` prototype in `tests/integration/test_lock_with_real_registry.py` with real `ClaudeMarketplaceFetcher`
- [ ] 13.2 Update integration test to verify plugin directory is cached (not just single .md file)
- [ ] 13.3 Add integration test: sync a plugin with multiple file types (agents, hooks, scripts)
- [ ] 13.4 Update e2e tests for new lock entry format (commit_sha)

## 14. Verification

- [ ] 14.1 Run `pytest -x` — all existing + new tests pass
- [ ] 14.2 Run `pyright` — no type errors
- [ ] 14.3 Run `ruff check .` — no lint issues
- [ ] 14.4 Run `ruff format --check .` — properly formatted
