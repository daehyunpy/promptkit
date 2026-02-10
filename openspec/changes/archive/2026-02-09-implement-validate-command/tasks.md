## 1. Domain: Validation Result Types

- [x] 1.1 Create `ValidationIssue` and `ValidationResult` value objects in `source/promptkit/domain/validation.py`
- [x] 1.2 Write tests for `ValidationResult.is_valid` logic (errors vs warnings)

## 2. Application: ValidateConfig Use Case

- [x] 2.1 Write failing test: config well-formed check (valid config returns no errors)
- [x] 2.2 Write failing test: config well-formed check (invalid YAML returns error)
- [x] 2.3 Write failing test: registry reference check (unknown registry returns error)
- [x] 2.4 Write failing test: lock freshness check (missing lock returns warning)
- [x] 2.5 Write failing test: lock freshness check (stale entry returns warning)
- [x] 2.6 Write failing test: lock freshness check (unlocked prompt returns warning)
- [x] 2.7 Write failing test: multiple issues collected in single result
- [x] 2.8 Implement `ValidateConfig` use case in `source/promptkit/app/validate.py`
- [x] 2.9 Verify all use case tests pass

## 3. CLI: Validate Command

- [x] 3.1 Write failing test: `test_validate_command_shows_in_help`
- [x] 3.2 Write failing test: `test_validate_succeeds_with_valid_config`
- [x] 3.3 Write failing test: `test_validate_fails_with_invalid_config`
- [x] 3.4 Write failing test: `test_validate_fails_without_config`
- [x] 3.5 Write failing test: `test_validate_shows_warnings_with_exit_zero`
- [x] 3.6 Implement `validate` command in `cli.py`
- [x] 3.7 Verify all new and existing tests pass
