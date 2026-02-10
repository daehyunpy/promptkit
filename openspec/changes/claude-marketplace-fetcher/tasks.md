## 1. Update PromptFetcher protocol and existing implementations

- [ ] 1.1 Change `PromptFetcher.fetch()` return type from `Prompt` to `list[Prompt]` in `source/promptkit/domain/protocols.py`
- [ ] 1.2 Update `LocalFileFetcher.fetch()` to return `[Prompt(...)]` (single-element list) in `source/promptkit/infra/fetchers/local_file_fetcher.py`
- [ ] 1.3 Update `tests/infra/fetchers/test_local_file_fetcher.py` assertions for list return type

## 2. Update LockPrompts use case for list[Prompt]

- [ ] 2.1 Update remote prompt loop in `LockPrompts.execute()` to iterate `list[Prompt]` from `fetch()` in `source/promptkit/app/lock.py`
- [ ] 2.2 Update local prompt loop in `LockPrompts.execute()` to iterate `list[Prompt]` from `local_fetcher.fetch()`
- [ ] 2.3 Update `FakeFetcher` in `tests/app/test_lock.py` to return `list[Prompt]`
- [ ] 2.4 Run `pytest tests/app/test_lock.py tests/infra/fetchers/test_local_file_fetcher.py -v` — all existing tests pass

## 3. Implement ClaudeMarketplaceFetcher

- [ ] 3.1 Create `source/promptkit/infra/fetchers/claude_marketplace.py` with `ClaudeMarketplaceFetcher` class
- [ ] 3.2 Implement URL parsing: extract `owner`/`repo` from `https://github.com/{owner}/{repo}`, raise `SyncError` for invalid URLs
- [ ] 3.3 Implement `_fetch_marketplace_json()`: GET `.claude-plugin/marketplace.json` via Contents API, find plugin entry by name
- [ ] 3.4 Implement plugin directory discovery: list source dir via Contents API, recurse into category subdirs, collect `.md` files
- [ ] 3.5 Implement skills array handling: when plugin entry has `skills` array, fetch `SKILL.md` from each skill path
- [ ] 3.6 Implement source path construction: `{registry_name}/{category}/{filename}` for plugins, `{registry_name}/skills/{skill_name}` for skills
- [ ] 3.7 Implement `fetch(spec) -> list[Prompt]`: orchestrate marketplace lookup → directory discovery → content fetching → Prompt construction

## 4. Write unit tests for ClaudeMarketplaceFetcher

- [ ] 4.1 Create `tests/infra/fetchers/test_claude_marketplace.py` with mocked `httpx.Client`
- [ ] 4.2 Test: single-file plugin fetch (one agent `.md` file)
- [ ] 4.3 Test: multi-file plugin fetch (agents + commands subdirectories)
- [ ] 4.4 Test: skills repo structure (plugin with `skills` array → `SKILL.md` files)
- [ ] 4.5 Test: plugin not found in marketplace.json → `SyncError`
- [ ] 4.6 Test: network/HTTP failure → `SyncError`
- [ ] 4.7 Test: non-`.md` files and root-level files are ignored
- [ ] 4.8 Test: source path category routing correctness
- [ ] 4.9 Test: GitHub URL parsing (valid and invalid)

## 5. Wire fetchers in CLI

- [ ] 5.1 Add `_make_fetchers(registries)` helper in `source/promptkit/cli.py` mapping `CLAUDE_MARKETPLACE` registries to `ClaudeMarketplaceFetcher`
- [ ] 5.2 Update `_make_lock_use_case()` to load config, extract registries, and pass fetchers

## 6. Update integration tests

- [ ] 6.1 Replace `GitHubRegistryFetcher` prototype in `tests/integration/test_lock_with_real_registry.py` with real `ClaudeMarketplaceFetcher`
- [ ] 6.2 Update single-prompt integration test for new list-based fetch and source paths
- [ ] 6.3 Add multi-file plugin integration test (e.g., `feature-dev` producing multiple lock entries)

## 7. Verification

- [ ] 7.1 Run `pytest -x` — all 230+ existing tests pass
- [ ] 7.2 Run `pytest tests/infra/fetchers/test_claude_marketplace.py -v` — new unit tests pass
- [ ] 7.3 Run `pyright` — no type errors
- [ ] 7.4 Run `ruff check .` — no lint issues
- [ ] 7.5 Manual test: `cd temp && promptkit sync` succeeds with real registries
