## Why

Users need to verify their `promptkit.yaml` is well-formed and that referenced prompts exist before running `lock` or `sync`. Currently, errors are only discovered at lock/build time with potentially confusing messages. A dedicated `promptkit validate` command provides fast, offline feedback — catching config errors, missing prompts, and stale lock files before they cause failures downstream.

## What Changes

- Add `ValidateConfig` use case in the application layer that checks:
  - Config is well-formed YAML with required fields (leverages existing `YamlLoader` validation)
  - Referenced registries are defined when prompts reference them
  - Local prompts referenced in lock file exist in `prompts/` directory
  - Lock file freshness: config hasn't changed since last lock (optional staleness check)
- Add `promptkit validate` CLI command that runs the validation use case
- Report all validation issues (not just the first one) for a good developer experience

## Capabilities

### New Capabilities
- `validate-config`: Application-layer use case that validates promptkit.yaml, checks prompt references, and detects lock file staleness
- `cli-validate-command`: CLI command that exposes the validate use case

### Modified Capabilities

(none)

## Impact

- `source/promptkit/app/validate.py` — new ValidateConfig use case
- `source/promptkit/cli.py` — add `validate` command
- `tests/app/test_validate.py` — unit tests for use case
- `tests/test_cli.py` — CLI-level tests for validate command
- No new dependencies — reuses existing `YamlLoader`, `LockFile`, `FileSystem`
