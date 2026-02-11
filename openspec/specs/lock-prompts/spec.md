## Requirements

### Requirement: LockEntry supports commit SHA for registry plugins
The `LockEntry` value object SHALL have an optional `commit_sha` field. Registry plugins use commit SHA for versioning. Local plugins continue using `content_hash` only.

#### Scenario: Lock entry for registry plugin
- **WHEN** a `LockEntry` is created for a registry plugin
- **THEN** `commit_sha` is set to the GitHub commit SHA string
- **AND** `content_hash` is `""` (empty string — registry plugins use commit SHA, not content hash)

#### Scenario: Lock entry for local plugin
- **WHEN** a `LockEntry` is created for a local plugin
- **THEN** `commit_sha` is `None`
- **AND** `content_hash` is the SHA256 hash of the plugin's file contents

#### Scenario: Backward compatibility
- **WHEN** a lock file without `commit_sha` fields is deserialized
- **THEN** all entries parse correctly with `commit_sha` as `None`

### Requirement: LockPrompts uses single code path for all plugins
The `LockPrompts` use case SHALL use a single code path for both local and registry plugins. Every spec is fetched via `PluginFetcher.fetch()`, producing a `Plugin` manifest and one `LockEntry`.

#### Scenario: Lock a registry plugin
- **WHEN** `execute()` is called with a config containing one registry spec `registry/plugin-name`
- **AND** a plugin fetcher for that registry is provided
- **THEN** the fetcher downloads the plugin directory to cache
- **AND** one `LockEntry` is written with the plugin name, source, commit SHA, `content_hash=""`, and timestamp

#### Scenario: Lock a local plugin (single .md file)
- **WHEN** `execute()` is called and `prompts/` contains `my-rule.md`
- **THEN** the local plugin fetcher returns a `Plugin` manifest
- **AND** a `LockEntry` with source `local/my-rule`, content hash, and `commit_sha=None` is written

#### Scenario: Lock a local plugin (directory with mixed files)
- **WHEN** `execute()` is called and `prompts/my-skill/` contains `SKILL.md` and `scripts/check.sh`
- **THEN** the local plugin fetcher returns a `Plugin` manifest with both files listed
- **AND** a `LockEntry` with source `local/my-skill`, content hash, and `commit_sha=None` is written

#### Scenario: Lock multiple plugins from different registries
- **WHEN** `execute()` is called with multiple specs from different registries
- **THEN** each spec is fetched from its respective registry's fetcher
- **AND** one lock entry per spec is recorded

#### Scenario: No fetcher available for registry
- **WHEN** a prompt spec references a registry with no registered fetcher
- **THEN** a `SyncError` is raised indicating the unsupported registry

#### Scenario: Plugin already cached with same commit SHA
- **WHEN** `execute()` is called and the lock file already has an entry with the same commit SHA
- **THEN** the fetcher is still called (to get the latest SHA) but the download is skipped if SHA matches
- **AND** the existing lock entry timestamp is preserved

#### Scenario: No local plugins
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

### Requirement: BuildArtifacts uses single code path for all plugins
The `BuildArtifacts` use case SHALL resolve the source directory for each lock entry and copy file trees to platform output directories.

#### Scenario: Build with registry plugin
- **WHEN** `execute()` is called and the lock file contains a registry plugin entry with `commit_sha`
- **THEN** the source dir is resolved to `.promptkit/cache/plugins/{registry}/{plugin}/{sha}/`
- **AND** files are copied to the platform output directory with appropriate directory mapping

#### Scenario: Build with local plugin
- **WHEN** the lock file contains a local plugin entry (no `commit_sha`)
- **THEN** the source dir is resolved to `prompts/`
- **AND** files are copied to the platform output directory with appropriate directory mapping

#### Scenario: Plugin cache missing
- **WHEN** the lock file has a `commit_sha` but the cache directory doesn't exist
- **THEN** a `BuildError` is raised suggesting `promptkit lock` to re-fetch
