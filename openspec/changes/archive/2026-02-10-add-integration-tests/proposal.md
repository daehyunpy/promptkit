## Why

The MVP is feature-complete (Phases 1-8), but integration test coverage is minimal — only `lock` has real integration tests (4 tests against GitHub registry). The remaining commands (`init`, `build`, `sync`, `validate`) lack end-to-end integration tests that exercise the full stack from CLI invocation through to real file system artifacts. Adding integration tests now catches cross-layer wiring bugs, validates real-world workflows, and builds confidence for future changes.

## What Changes

- Add end-to-end integration tests for the `init` command (real file scaffolding)
- Add end-to-end integration tests for the `build` command (real config → real artifacts)
- Add end-to-end integration tests for the `sync` command (full lock + build pipeline)
- Add end-to-end integration tests for the `validate` command (real config validation scenarios)
- Introduce shared integration test fixtures (reusable project scaffolds, config helpers)

## Capabilities

### New Capabilities
- `integration-testing`: End-to-end integration tests for all CLI commands, exercising real file I/O, config loading, caching, and artifact generation without mocks

### Modified Capabilities

## Impact

- `tests/integration/` — new test files for each command
- `tests/conftest.py` — shared fixtures for integration test scaffolding
- No changes to production source code
- No new dependencies
