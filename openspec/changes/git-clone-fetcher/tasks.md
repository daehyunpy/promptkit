## 1. GitRegistryClone Infrastructure

- [ ] 1.1 Create `GitRegistryClone` class in `source/promptkit/infra/fetchers/git_registry_clone.py` with constructor accepting `registry_name`, `registry_url`, and `registries_dir` (Path to `.promptkit/registries/`)
- [ ] 1.2 Implement git availability check — run `git --version` at construction, raise `SyncError` if not found
- [ ] 1.3 Implement `ensure_up_to_date()` — clone if no local clone exists, pull if clone exists, delete-and-reclone if pull fails
- [ ] 1.4 Implement `get_commit_sha()` — run `git rev-parse HEAD` in clone dir, return full 40-char SHA
- [ ] 1.5 Implement `clone_dir` property — return `Path` to `.promptkit/registries/{registry_name}/`
- [ ] 1.6 Implement `_run_git()` helper — wraps `subprocess.run`, raises `SyncError` with stderr on failure

## 2. GitRegistryClone Tests

- [ ] 2.1 Test construction validates git availability (mock subprocess to simulate git not found)
- [ ] 2.2 Test `ensure_up_to_date()` clones when no local directory exists (use a real temp git repo)
- [ ] 2.3 Test `ensure_up_to_date()` pulls when clone already exists
- [ ] 2.4 Test `ensure_up_to_date()` recovers from corrupt clone (delete + re-clone)
- [ ] 2.5 Test `get_commit_sha()` returns correct SHA from local clone
- [ ] 2.6 Test git errors are wrapped in `SyncError` with stderr message

## 3. Rewrite ClaudeMarketplaceFetcher

- [ ] 3.1 Replace `httpx.Client` constructor parameter with `GitRegistryClone` parameter (`clone`)
- [ ] 3.2 Replace `_fetch_marketplace_json()` — read `.claude-plugin/marketplace.json` from `clone.clone_dir` via filesystem
- [ ] 3.3 Replace `_get_latest_commit_sha()` — delegate to `clone.get_commit_sha()`
- [ ] 3.4 Replace `_list_and_download_directory()` — use `shutil.copytree` / filesystem walk from clone dir to cache dir
- [ ] 3.5 Replace `_handle_skills_array()` — copy skill directories from clone instead of HTTP download
- [ ] 3.6 Add `clone.ensure_up_to_date()` call at the start of `_do_fetch()`
- [ ] 3.7 Remove `_download_file()` method and `httpx` import
- [ ] 3.8 Add error handling for missing `marketplace.json` in clone (raise `SyncError`)
- [ ] 3.9 Add error handling for missing plugin directory in clone (raise `SyncError`)

## 4. Update ClaudeMarketplaceFetcher Tests

- [ ] 4.1 Create a `FakeGitRegistryClone` test double that uses a temp directory with pre-populated files
- [ ] 4.2 Rewrite `test_fetch_plugin_with_relative_source` using `FakeGitRegistryClone`
- [ ] 4.3 Rewrite `test_fetch_plugin_with_mixed_files` (agents, hooks, scripts)
- [ ] 4.4 Rewrite `test_fetch_plugin_with_skills_array`
- [ ] 4.5 Rewrite `test_plugin_not_found_error`
- [ ] 4.6 Rewrite `test_external_source_rejected`
- [ ] 4.7 Rewrite `test_cache_hit_skips_download` — verify no file copy when cache exists
- [ ] 4.8 Add test for missing `marketplace.json` in clone
- [ ] 4.9 Add test for missing plugin directory in clone

## 5. CLI Wiring Update

- [ ] 5.1 Update `_make_plugin_fetchers()` in `cli.py` — construct `GitRegistryClone` and pass to `ClaudeMarketplaceFetcher`
- [ ] 5.2 Ensure `registries_dir` defaults to `{project_dir}/.promptkit/registries/`

## 6. Remove httpx Dependency

- [ ] 6.1 Remove `httpx` from `dependencies` in `pyproject.toml`
- [ ] 6.2 Run `uv sync` to update `uv.lock`
- [ ] 6.3 Verify no remaining `import httpx` in `source/` (only in tests or openspec artifacts is acceptable)

## 7. Gitignore and Init

- [ ] 7.1 Add `.promptkit/registries/` to project `.gitignore`
- [ ] 7.2 Update `promptkit init` scaffold to include `.promptkit/registries/` in generated `.gitignore`
