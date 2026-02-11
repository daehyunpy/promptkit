## ADDED Requirements

### Requirement: CLI exposes clean command
The CLI SHALL expose a `promptkit clean` command that removes all promptkit-managed build artifacts.

#### Scenario: Running clean with default options
- **WHEN** user runs `promptkit clean`
- **THEN** all managed build artifacts are removed, manifests are deleted, and the message "Cleaned build artifacts" is printed to stdout

#### Scenario: Running clean when nothing to clean
- **WHEN** user runs `promptkit clean` with no manifests present
- **THEN** the message "Nothing to clean" is printed to stdout and the exit code is 0

### Requirement: CLI clean command accepts --cache flag
The `promptkit clean` command SHALL accept a `--cache` flag that additionally removes the `.promptkit/cache/` directory.

#### Scenario: Running clean with --cache flag
- **WHEN** user runs `promptkit clean --cache`
- **THEN** managed build artifacts are removed AND the plugin cache directory is removed, with the message "Cleaned build artifacts and cache"

### Requirement: CLI clean command reports errors
The `promptkit clean` command SHALL catch errors during cleanup and report them to stderr with exit code 1.

#### Scenario: Permission error during clean
- **WHEN** a managed file cannot be deleted due to permissions
- **THEN** an error message is printed to stderr and the command exits with code 1
