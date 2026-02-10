## Context

promptkit has 230 tests, but integration coverage is uneven. Only the `lock` command has true integration tests (4 tests that hit a real GitHub registry). The `init`, `build`, `sync`, and `validate` commands have unit tests and CLI smoke tests but no end-to-end integration tests that exercise the full stack with real file I/O, real config parsing, real caching, and real artifact generation.

The existing integration test pattern (`tests/integration/test_lock_with_real_registry.py`) establishes a solid template: create a temporary project directory, write real config files, wire up real use cases, and assert on real file system output.

## Goals / Non-Goals

**Goals:**
- End-to-end integration tests for `init`, `build`, `sync`, and `validate` commands
- Tests exercise real infrastructure (FileSystem, YamlLoader, LockFile, PromptCache, builders) — no mocks
- Tests use the CLI runner interface (CliRunner from typer) to test from the user's perspective
- Shared fixtures to reduce boilerplate across integration test modules
- All integration tests marked with `@pytest.mark.integration` for selective execution

**Non-Goals:**
- Network-dependent tests (those already exist for `lock`; new tests use only local prompts)
- Performance or load testing
- Testing third-party libraries (typer, pydantic, ruamel)
- Refactoring production code to accommodate tests

## Decisions

### 1. CLI-level integration tests via CliRunner

**Decision:** Integration tests invoke commands through typer's `CliRunner`, the same way the existing CLI tests do, but with real file system state instead of minimal stubs.

**Rationale:** This tests the full wiring: CLI handler → use case → infrastructure. It catches dependency injection bugs, path resolution issues, and cross-layer wiring problems. The alternative — calling use case `.execute()` directly — would miss the CLI wiring layer.

### 2. Local-only prompts (no network dependency)

**Decision:** New integration tests use local prompts in `prompts/` directory only. No remote registry fetching.

**Rationale:** Network tests are flaky and slow. The existing `test_lock_with_real_registry.py` covers the network path. New tests focus on the file-system-based workflows (init scaffolding, lock of local prompts, build artifact generation, validate against real config/lock files). This keeps the new tests fast and reliable.

### 3. Shared fixtures in `tests/integration/conftest.py`

**Decision:** Create a shared conftest for integration tests with reusable project scaffolding fixtures.

**Rationale:** Each integration test needs a tmp directory with config files, prompt files, cache dirs, etc. A shared `scaffold_project` fixture avoids duplicating this setup across 4+ test files. The existing `tests/conftest.py` stays minimal; integration-specific fixtures go in `tests/integration/conftest.py`.

### 4. One test file per command

**Decision:** Create separate test files: `test_init_e2e.py`, `test_build_e2e.py`, `test_sync_e2e.py`, `test_validate_e2e.py`.

**Rationale:** Mirrors the existing unit test structure (one file per use case). Keeps test files focused and easy to run selectively. The `_e2e` suffix distinguishes them from any future integration tests added for other purposes.

## Risks / Trade-offs

- **[Test speed]** Integration tests with real file I/O are slower than pure unit tests (~10-50ms vs ~1ms per test). Mitigation: tests are still fast enough to run on every commit; the `@pytest.mark.integration` marker allows skipping them if needed.
- **[Fixture coupling]** Shared fixtures could become a maintenance burden if tests diverge in setup needs. Mitigation: keep fixtures minimal (project dir + basic config); let each test customize what it needs.
- **[CWD dependency]** CLI commands use `Path.cwd()` internally, requiring `monkeypatch.chdir()` in tests. Mitigation: this pattern is already established in `test_cli.py` and works reliably.
