## ADDED Requirements

### Requirement: CLI exposes validate command
The CLI SHALL expose a `promptkit validate` command that verifies the config is well-formed and prompts are properly referenced.

#### Scenario: Config is valid
- **WHEN** `promptkit validate` is run with a valid config and fresh lock
- **THEN** a success message is printed to stdout
- **AND** the exit code is 0

#### Scenario: Config has errors
- **WHEN** `promptkit validate` is run and validation errors are found
- **THEN** each error is printed to stderr
- **AND** the exit code is 1

#### Scenario: Config has warnings only
- **WHEN** `promptkit validate` is run and only warnings are found (no errors)
- **THEN** each warning is printed to stdout
- **AND** the exit code is 0

#### Scenario: Missing config file
- **WHEN** `promptkit validate` is run in a directory without `promptkit.yaml`
- **THEN** an error message is printed to stderr
- **AND** the exit code is 1

### Requirement: Validate command uses current working directory
The `validate` CLI command SHALL use `Path.cwd()` as the project directory, consistent with other commands.

#### Scenario: Validate reads from cwd
- **WHEN** `promptkit validate` is run
- **THEN** it reads `promptkit.yaml` and `promptkit.lock` from the current working directory
