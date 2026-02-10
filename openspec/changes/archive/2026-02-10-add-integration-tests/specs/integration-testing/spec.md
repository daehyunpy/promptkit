## ADDED Requirements

### Requirement: Init command creates complete project scaffold
The init command integration test SHALL invoke `promptkit init` via CliRunner and verify all expected files and directories are created on the real file system.

#### Scenario: Init creates all expected files and directories
- **WHEN** `promptkit init` is invoked in an empty directory via CliRunner
- **THEN** the following exist on disk: `promptkit.yaml`, `promptkit.lock`, `.promptkit/cache/`, `prompts/`, `.cursor/`, `.claude/`, `.gitignore`
- **AND** `promptkit.yaml` is valid YAML parseable by YamlLoader
- **AND** the exit code is 0

#### Scenario: Init fails in already-initialized directory
- **WHEN** `promptkit init` is invoked in a directory that already has `promptkit.yaml`
- **THEN** the exit code is 1
- **AND** stderr contains an error message

### Requirement: Build command generates platform artifacts from local prompts
The build integration test SHALL exercise the full pipeline: config loading, lock file reading, cache/local content reading, and artifact generation for both Cursor and Claude Code platforms.

#### Scenario: Build generates Cursor rules file from local prompt
- **WHEN** a project has a local prompt in `prompts/`, a valid config targeting cursor, and a matching lock file
- **AND** `promptkit build` is invoked via CliRunner
- **THEN** a `.cursor/rules/` directory contains the prompt as a `.mdc` file
- **AND** the exit code is 0

#### Scenario: Build generates Claude Code commands from local prompt
- **WHEN** a project has a local prompt in `prompts/`, a valid config targeting claude-code, and a matching lock file
- **AND** `promptkit build` is invoked via CliRunner
- **THEN** a `.claude/commands/` directory contains the prompt as a `.md` file
- **AND** the exit code is 0

#### Scenario: Build generates artifacts for both platforms
- **WHEN** a project has a local prompt and config targeting both cursor and claude-code
- **AND** `promptkit build` is invoked via CliRunner
- **THEN** both `.cursor/rules/` and `.claude/commands/` contain the prompt artifact
- **AND** the exit code is 0

#### Scenario: Build fails without lock file
- **WHEN** a project has config but no lock file
- **AND** `promptkit build` is invoked via CliRunner
- **THEN** the exit code is 1
- **AND** stderr contains an error about missing lock file

### Requirement: Sync command performs lock and build in sequence
The sync integration test SHALL verify that `promptkit sync` fetches local prompts, writes a lock file, and generates platform artifacts in a single operation.

#### Scenario: Sync locks and builds local prompts end-to-end
- **WHEN** a project has a local prompt in `prompts/` and a valid config
- **AND** `promptkit sync` is invoked via CliRunner
- **THEN** `promptkit.lock` exists with an entry for the local prompt
- **AND** platform artifacts are generated in the configured output directories
- **AND** the exit code is 0

#### Scenario: Sync with multiple local prompts
- **WHEN** a project has multiple local prompts and config referencing all of them
- **AND** `promptkit sync` is invoked via CliRunner
- **THEN** `promptkit.lock` contains entries for all prompts
- **AND** platform artifacts exist for each prompt
- **AND** the exit code is 0

### Requirement: Validate command checks config and lock consistency
The validate integration test SHALL exercise real config parsing, registry reference checking, and lock freshness checking against real files.

#### Scenario: Validate passes on well-formed config with fresh lock
- **WHEN** a project has valid config, matching lock file, and local prompts
- **AND** `promptkit validate` is invoked via CliRunner
- **THEN** stdout contains "Config is valid"
- **AND** the exit code is 0

#### Scenario: Validate reports missing lock file as warning
- **WHEN** a project has valid config but no lock file
- **AND** `promptkit validate` is invoked via CliRunner
- **THEN** output contains a warning about missing lock file
- **AND** the exit code is 0 (warnings do not cause failure)

#### Scenario: Validate reports undefined registry as error
- **WHEN** a project has config referencing an undefined registry
- **AND** `promptkit validate` is invoked via CliRunner
- **THEN** stderr contains an error about undefined registry
- **AND** the exit code is 1

#### Scenario: Validate reports stale lock entries as warning
- **WHEN** a project has a lock file with entries not present in config
- **AND** `promptkit validate` is invoked via CliRunner
- **THEN** output contains a warning about stale entries

### Requirement: Shared integration test fixtures
The integration test suite SHALL provide reusable fixtures for project scaffolding to reduce duplication across test files.

#### Scenario: Scaffold fixture creates minimal project structure
- **WHEN** the `project_dir` fixture is used in an integration test
- **THEN** a temporary directory exists with `prompts/` and `.promptkit/cache/` subdirectories

#### Scenario: Scaffold with config fixture writes valid promptkit.yaml
- **WHEN** a test writes a config YAML string to the project directory
- **THEN** the file is parseable by YamlLoader and produces a valid LoadedConfig
