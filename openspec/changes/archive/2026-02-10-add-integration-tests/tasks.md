## 1. Shared Fixtures

- [x] 1.1 Create `tests/integration/conftest.py` with `project_dir` fixture (tmp dir with `prompts/` and `.promptkit/cache/`)
- [x] 1.2 Add helper to write `promptkit.yaml` config and local prompt files to the project dir

## 2. Init Integration Tests

- [x] 2.1 Create `tests/integration/test_init_e2e.py` with test that init creates all expected files and directories
- [x] 2.2 Add test that init fails in an already-initialized directory

## 3. Build Integration Tests

- [x] 3.1 Create `tests/integration/test_build_e2e.py` with test for Cursor artifact generation from local prompt
- [x] 3.2 Add test for Claude Code artifact generation from local prompt
- [x] 3.3 Add test for dual-platform artifact generation
- [x] 3.4 Add test that build fails without lock file

## 4. Sync Integration Tests

- [x] 4.1 Create `tests/integration/test_sync_e2e.py` with test for end-to-end lock + build of a local prompt
- [x] 4.2 Add test for sync with multiple local prompts

## 5. Validate Integration Tests

- [x] 5.1 Create `tests/integration/test_validate_e2e.py` with test for valid config with fresh lock
- [x] 5.2 Add test for missing lock file warning
- [x] 5.3 Add test for undefined registry error
- [x] 5.4 Add test for stale lock entries warning
