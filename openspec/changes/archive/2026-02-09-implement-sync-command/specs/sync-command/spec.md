## ADDED Requirements

### Requirement: CLI exposes sync command
The CLI SHALL expose a `promptkit sync` command that fetches prompts, updates the lock file, and generates platform artifacts in a single operation.

#### Scenario: Successful sync
- **WHEN** `promptkit sync` is run in a directory with a valid `promptkit.yaml`
- **THEN** prompts are fetched and cached
- **AND** `promptkit.lock` is updated
- **AND** platform artifacts are generated in configured output directories
- **AND** a success message is printed to stdout

#### Scenario: Missing config file
- **WHEN** `promptkit sync` is run in a directory without `promptkit.yaml`
- **THEN** an error message is printed to stderr
- **AND** the exit code is 1

#### Scenario: Lock phase fails
- **WHEN** `promptkit sync` is run and the lock phase fails (e.g., fetch error)
- **THEN** the build phase SHALL NOT be attempted
- **AND** a `SyncError` message is printed to stderr
- **AND** the exit code is 1

#### Scenario: Build phase fails
- **WHEN** `promptkit sync` is run, lock succeeds, but the build phase fails
- **THEN** the lock file SHALL be preserved (lock was successful)
- **AND** a `BuildError` message is printed to stderr
- **AND** the exit code is 1

### Requirement: Sync command uses current working directory
The `sync` CLI command SHALL use `Path.cwd()` as the project directory, consistent with other commands.

#### Scenario: Sync reads from cwd
- **WHEN** `promptkit sync` is run
- **THEN** it reads `promptkit.yaml` from the current working directory
- **AND** writes `promptkit.lock` and artifacts relative to the current working directory

### Requirement: Sync composes lock and build sequentially
The `sync` command SHALL execute `LockPrompts` followed by `BuildArtifacts` sequentially. It SHALL NOT introduce a new application-layer use case.

#### Scenario: Sequential execution
- **WHEN** `promptkit sync` is run
- **THEN** `LockPrompts.execute()` runs first
- **AND** `BuildArtifacts.execute()` runs after lock completes successfully

### Requirement: Sync displays progress messages
The `sync` command SHALL display progress messages indicating which phase is executing.

#### Scenario: Progress output
- **WHEN** `promptkit sync` is run successfully
- **THEN** the output indicates locking and building phases
- **AND** a final success message is displayed
