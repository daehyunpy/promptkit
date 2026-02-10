## ADDED Requirements

### Requirement: LockPrompts fetches and locks remote prompts
The `LockPrompts` use case SHALL fetch each remote prompt declared in `promptkit.yaml`, cache the content, and record a `LockEntry`.

#### Scenario: Lock a single remote prompt
- **WHEN** `execute()` is called with a config containing one remote prompt spec `registry/prompt-name`
- **AND** a fetcher for that registry is provided
- **THEN** the fetcher is called with the prompt spec
- **AND** the fetched content is stored in the cache
- **AND** a `LockEntry` is written to `promptkit.lock` with name, source, SHA256 hash, and current timestamp

#### Scenario: Lock multiple remote prompts
- **WHEN** `execute()` is called with a config containing multiple remote prompt specs from different registries
- **THEN** each prompt is fetched from its respective registry's fetcher
- **AND** all are cached and recorded in the lock file

#### Scenario: No fetcher available for registry
- **WHEN** `execute()` is called and a prompt spec references a registry with no registered fetcher
- **THEN** a `SyncError` is raised indicating the unsupported registry

### Requirement: LockPrompts discovers and locks local prompts
The `LockPrompts` use case SHALL discover all prompts in `prompts/`, fetch their content, cache it, and record lock entries with `local/<name>` source.

#### Scenario: Lock local prompts
- **WHEN** `execute()` is called and `prompts/` contains `my-rule.md`
- **THEN** the local prompt is fetched, cached, and a `LockEntry` with source `local/my-rule` is written

#### Scenario: No local prompts
- **WHEN** `execute()` is called and `prompts/` is empty
- **THEN** no local lock entries are created (not an error)

### Requirement: LockPrompts preserves timestamps for unchanged content
The `LockPrompts` use case SHALL preserve the `fetched_at` timestamp from the existing lock file when a prompt's content hash has not changed.

#### Scenario: Content unchanged since last lock
- **WHEN** `execute()` is called and a prompt's content hash matches the existing lock entry
- **THEN** the existing `fetched_at` timestamp is preserved in the new lock file

#### Scenario: Content changed since last lock
- **WHEN** `execute()` is called and a prompt's content hash differs from the existing lock entry
- **THEN** the `fetched_at` timestamp is updated to the current time

#### Scenario: New prompt not in existing lock
- **WHEN** `execute()` is called and a prompt has no existing lock entry
- **THEN** the `fetched_at` timestamp is set to the current time

### Requirement: LockPrompts reads config and writes lock file
The `LockPrompts` use case SHALL read `promptkit.yaml` to determine what to lock and write the result to `promptkit.lock`.

#### Scenario: Config file is read
- **WHEN** `execute(project_dir)` is called
- **THEN** `promptkit.yaml` is read from `project_dir` and parsed via `YamlLoader`

#### Scenario: Lock file is written
- **WHEN** locking completes successfully
- **THEN** `promptkit.lock` is written to `project_dir` with all lock entries serialized

#### Scenario: Existing lock file is loaded for comparison
- **WHEN** `execute()` is called and `promptkit.lock` exists in `project_dir`
- **THEN** existing lock entries are loaded and used for timestamp preservation

#### Scenario: No existing lock file
- **WHEN** `execute()` is called and no `promptkit.lock` exists
- **THEN** all prompts are treated as new (fresh timestamps)

### Requirement: LockPrompts removes stale lock entries
The `LockPrompts` use case SHALL NOT include lock entries for prompts that are no longer declared in config or present in `prompts/`.

#### Scenario: Prompt removed from config
- **WHEN** a prompt was in the previous lock file but is no longer in `promptkit.yaml` or `prompts/`
- **THEN** its lock entry is not included in the updated lock file
