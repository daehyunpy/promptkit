## 1. Extract Shared CLI Wiring

- [x] 1.1 Extract helper functions in `cli.py` for creating shared infrastructure (`FileSystem`, `YamlLoader`, `LockFile`, `PromptCache`, `LocalFileFetcher`, builders dict)
- [x] 1.2 Refactor `lock` command to use extracted helpers
- [x] 1.3 Refactor `build` command to use extracted helpers
- [x] 1.4 Verify existing CLI tests still pass after refactor

## 2. Implement Sync Command

- [x] 2.1 Write failing test: `test_sync_command_shows_in_help`
- [x] 2.2 Write failing test: `test_sync_succeeds_with_local_prompts` (locks + builds)
- [x] 2.3 Write failing test: `test_sync_fails_without_config`
- [x] 2.4 Write failing test: `test_sync_lock_failure_skips_build`
- [x] 2.5 Implement `sync` command in `cli.py` that calls `LockPrompts.execute()` then `BuildArtifacts.execute()`
- [x] 2.6 Add progress messages ("Locking...", "Building...", final success)
- [x] 2.7 Verify all new and existing tests pass
