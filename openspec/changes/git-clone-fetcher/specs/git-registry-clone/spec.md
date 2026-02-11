## ADDED Requirements

### Requirement: GitRegistryClone clones a registry repository with shallow depth
The `GitRegistryClone` SHALL clone a GitHub repository using `git clone --depth 1` to a local directory at `.promptkit/registries/{registry_name}/`. The clone SHALL use HTTPS URL format.

#### Scenario: First clone of a registry
- **WHEN** `ensure_up_to_date()` is called and no local clone exists at `.promptkit/registries/{registry_name}/`
- **THEN** `git clone --depth 1 https://github.com/{owner}/{repo}.git` is executed into the registries directory
- **AND** the clone directory contains the repository files

#### Scenario: Clone directory already exists
- **WHEN** `ensure_up_to_date()` is called and the clone directory already exists with a valid `.git/` subdirectory
- **THEN** `git pull` is executed in the existing clone directory to fetch latest changes
- **AND** the clone is updated to the latest commit

### Requirement: GitRegistryClone recovers from corrupt clone state
The `GitRegistryClone` SHALL handle corrupt or invalid clone directories by deleting and re-cloning.

#### Scenario: Git pull fails on existing clone
- **WHEN** `ensure_up_to_date()` is called and the clone directory exists but `git pull` fails
- **THEN** the clone directory is deleted
- **AND** a fresh `git clone --depth 1` is performed
- **AND** the operation succeeds with a valid clone

#### Scenario: Clone directory exists but has no .git subdirectory
- **WHEN** `ensure_up_to_date()` is called and the directory exists but is not a git repository
- **THEN** the directory is deleted
- **AND** a fresh `git clone --depth 1` is performed

### Requirement: GitRegistryClone reports the current commit SHA
The `GitRegistryClone` SHALL return the HEAD commit SHA of the local clone using `git rev-parse HEAD`.

#### Scenario: Get commit SHA from clone
- **WHEN** `get_commit_sha()` is called after a successful clone or pull
- **THEN** the full 40-character commit SHA is returned

### Requirement: GitRegistryClone provides the clone directory path
The `GitRegistryClone` SHALL expose the local clone directory path so callers can read files directly from the filesystem.

#### Scenario: Access clone path
- **WHEN** `clone_dir` is accessed
- **THEN** it returns the `Path` to `.promptkit/registries/{registry_name}/`

### Requirement: GitRegistryClone validates git availability
The `GitRegistryClone` SHALL verify that the `git` CLI is available on PATH before attempting any operations.

#### Scenario: Git is available
- **WHEN** `GitRegistryClone` is constructed and `git --version` succeeds
- **THEN** construction succeeds normally

#### Scenario: Git is not installed
- **WHEN** `GitRegistryClone` is constructed and `git` is not found on PATH
- **THEN** a `SyncError` is raised with the message "git is required but not found on PATH. Install git to use registry plugins."

### Requirement: GitRegistryClone wraps git errors in SyncError
All git subprocess failures SHALL be wrapped in `SyncError` with the git stderr output included in the error message.

#### Scenario: Clone fails due to network error
- **WHEN** `git clone` fails (e.g., network unreachable, repository not found)
- **THEN** a `SyncError` is raised containing the git stderr message

#### Scenario: Clone fails due to invalid repository URL
- **WHEN** `git clone` is called with a URL that does not point to a valid repository
- **THEN** a `SyncError` is raised with the git error message
