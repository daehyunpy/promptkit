## MODIFIED Requirements

### Requirement: LockPrompts fetches and locks remote prompts
The `LockPrompts` use case SHALL fetch each remote prompt declared in `promptkit.yaml`, cache the content, and record a `LockEntry`. A single `fetch(spec)` call MAY return multiple `Prompt` objects (for multi-file plugins), and each SHALL be independently cached and locked.

#### Scenario: Lock a single remote prompt
- **WHEN** `execute()` is called with a config containing one remote prompt spec `registry/prompt-name`
- **AND** a fetcher for that registry is provided
- **THEN** the fetcher is called with the prompt spec
- **AND** for each `Prompt` in the returned list, the content is stored in the cache
- **AND** a `LockEntry` is written to `promptkit.lock` for each prompt with name, source, SHA256 hash, and current timestamp

#### Scenario: Lock multiple remote prompts
- **WHEN** `execute()` is called with a config containing multiple remote prompt specs from different registries
- **THEN** each prompt spec is fetched from its respective registry's fetcher
- **AND** all returned prompts (potentially multiple per spec) are cached and recorded in the lock file

#### Scenario: No fetcher available for registry
- **WHEN** `execute()` is called and a prompt spec references a registry with no registered fetcher
- **THEN** a `SyncError` is raised indicating the unsupported registry

#### Scenario: Multi-file plugin produces multiple lock entries
- **WHEN** `execute()` is called with a spec for a multi-file plugin (e.g., `feature-dev` with 3 agents + 1 command)
- **AND** the fetcher returns a list of 4 `Prompt` objects
- **THEN** 4 separate `LockEntry` records are written to the lock file
- **AND** each has its own source path, content hash, and timestamp

### Requirement: LockPrompts discovers and locks local prompts
The `LockPrompts` use case SHALL discover all prompts in `prompts/`, fetch their content via `LocalFileFetcher` (which returns `list[Prompt]`), cache it, and record lock entries with `local/<name>` source.

#### Scenario: Lock local prompts
- **WHEN** `execute()` is called and `prompts/` contains `my-rule.md`
- **THEN** the local prompt is fetched (returning a single-element list), cached, and a `LockEntry` with source `local/my-rule` is written

#### Scenario: No local prompts
- **WHEN** `execute()` is called and `prompts/` is empty
- **THEN** no local lock entries are created (not an error)
