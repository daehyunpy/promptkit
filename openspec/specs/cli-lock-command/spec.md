## ADDED Requirements

### Requirement: CLI exposes lock command
The CLI SHALL expose a `promptkit lock` command that fetches prompts and updates the lock file.

#### Scenario: Successful lock
- **WHEN** `promptkit lock` is run in a directory with a valid `promptkit.yaml`
- **THEN** prompts are fetched, cached, and `promptkit.lock` is updated
- **AND** a success message is printed to stdout

#### Scenario: Missing config file
- **WHEN** `promptkit lock` is run in a directory without `promptkit.yaml`
- **THEN** an error message is printed to stderr
- **AND** the exit code is 1

#### Scenario: Fetch error
- **WHEN** `promptkit lock` is run and a prompt fetch fails
- **THEN** a `SyncError` message is printed to stderr
- **AND** the exit code is 1

### Requirement: Lock command uses current working directory
The `lock` CLI command SHALL use `Path.cwd()` as the project directory, consistent with the `init` command pattern.

#### Scenario: Lock reads from cwd
- **WHEN** `promptkit lock` is run
- **THEN** it reads `promptkit.yaml` from the current working directory
- **AND** writes `promptkit.lock` to the current working directory
