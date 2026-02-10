# Integration Tests

Integration tests verify promptkit works correctly with real external dependencies.

## Test Categories

### `@pytest.mark.integration`
Tests that integrate multiple components together, potentially using real infrastructure.

### `@pytest.mark.network`
Tests that require network access to fetch data from external sources.

## Running Integration Tests

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run only integration tests (excludes network-dependent tests)
uv run pytest -m integration -v

# Run only network tests
uv run pytest -m network -v

# Skip integration/network tests (run only fast unit tests)
uv run pytest -m "not integration and not network" -v
```

## Test Files

### `test_lock_with_real_registry.py`
Tests the lock command with real GitHub registries:
- Fetches the `code-simplifier` agent from `claude-plugins-official`
- Verifies content caching, lock file generation, and hash computation
- Tests timestamp preservation on re-fetch
- Validates error handling for non-existent prompts

**Registry Used:** `claude-plugins-official` (https://github.com/anthropics/claude-plugins-official)

**Prompts Tested:**
- `code-simplifier` - Code simplification agent

## Adding New Integration Tests

When adding new integration tests:

1. Mark them appropriately:
   ```python
   @pytest.mark.integration
   @pytest.mark.network  # if requires network
   class TestMyIntegration:
       ...
   ```

2. Use fixtures for setup:
   - `project_dir` - Temporary project directory
   - `github_fetcher` - GitHub registry fetcher

3. Document what the test verifies in docstrings

4. Consider test runtime - integration tests are slower than unit tests

## CI/CD Considerations

Integration tests that depend on external services (like GitHub) may be:
- Slower than unit tests
- Subject to rate limits
- Dependent on network availability
- Flaky due to external service issues

Consider running them:
- In a separate CI job
- On a schedule rather than every commit
- With retries for network failures
