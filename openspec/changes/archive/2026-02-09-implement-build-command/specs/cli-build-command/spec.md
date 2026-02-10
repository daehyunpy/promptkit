## ADDED Requirements

### Requirement: CLI exposes build command
The CLI SHALL expose a `promptkit build` command that generates platform-specific artifacts from cached prompts.

#### Scenario: Successful build
- **WHEN** `promptkit build` is run in a project directory with a valid config and lock file
- **THEN** platform artifacts are generated
- **AND** a success message is printed to stdout

#### Scenario: Build with no lock file
- **WHEN** `promptkit build` is run in a project directory without `promptkit.lock`
- **THEN** an error message is printed to stderr
- **AND** the process exits with code 1

#### Scenario: Build with missing config
- **WHEN** `promptkit build` is run in a project directory without `promptkit.yaml`
- **THEN** an error message is printed to stderr
- **AND** the process exits with code 1

### Requirement: Build command wires up infrastructure
The `build` CLI command SHALL construct the `BuildArtifacts` use case with real infrastructure adapters (FileSystem, YamlLoader, LockFile, PromptCache, builders).

#### Scenario: Infrastructure is properly wired
- **WHEN** `promptkit build` is invoked
- **THEN** `BuildArtifacts` is constructed with `FileSystem`, `YamlLoader`, `LockFile`, `PromptCache`, and platform builders
- **AND** `execute()` is called with the current working directory
