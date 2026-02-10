## MODIFIED Requirements

### Requirement: LockEntry supports commit SHA for remote plugins
The `LockEntry` value object SHALL have an optional `commit_sha` field. Remote plugins use commit SHA for versioning. Local prompts continue using `content_hash` only.

#### Scenario: Lock entry for remote plugin
- **WHEN** a `LockEntry` is created for a remote plugin
- **THEN** `commit_sha` is set to the GitHub commit SHA string
- **AND** `content_hash` may be empty (files are on disk, not hashed individually)

#### Scenario: Lock entry for local prompt
- **WHEN** a `LockEntry` is created for a local prompt
- **THEN** `commit_sha` is `None`
- **AND** `content_hash` is the SHA256 of the prompt content

#### Scenario: Backward compatibility
- **WHEN** a lock file without `commit_sha` fields is deserialized
- **THEN** all entries parse correctly with `commit_sha` as `None`

### Requirement: LockPrompts fetches and locks remote plugins
The `LockPrompts` use case SHALL fetch each remote plugin declared in `promptkit.yaml` via `PluginFetcher`, download to cache, and record one `LockEntry` per plugin.

#### Scenario: Lock a single remote plugin
- **WHEN** `execute()` is called with a config containing one remote spec `registry/plugin-name`
- **AND** a plugin fetcher for that registry is provided
- **THEN** the fetcher downloads the plugin directory to cache
- **AND** one `LockEntry` is written with the plugin name, source, commit SHA, and timestamp

#### Scenario: Lock multiple remote plugins from different registries
- **WHEN** `execute()` is called with multiple remote specs from different registries
- **THEN** each spec is fetched from its respective registry's fetcher
- **AND** one lock entry per spec is recorded

#### Scenario: No fetcher available for registry
- **WHEN** a prompt spec references a registry with no registered fetcher
- **THEN** a `SyncError` is raised indicating the unsupported registry

#### Scenario: Plugin already cached with same commit SHA
- **WHEN** `execute()` is called and the lock file already has an entry with the same commit SHA
- **THEN** the fetcher is still called (to get the latest SHA) but the download is skipped if SHA matches
- **AND** the existing lock entry timestamp is preserved

### Requirement: LockPrompts discovers and locks local prompts (unchanged)
The `LockPrompts` use case SHALL continue to discover all prompts in `prompts/`, fetch their content via `LocalFileFetcher`, cache it, and record lock entries with `local/<name>` source.

#### Scenario: Lock local prompts
- **WHEN** `execute()` is called and `prompts/` contains `my-rule.md`
- **THEN** the local prompt is fetched, cached, and a `LockEntry` with source `local/my-rule` and content hash is written

#### Scenario: No local prompts
- **WHEN** `execute()` is called and `prompts/` is empty
- **THEN** no local lock entries are created (not an error)

### Requirement: BuildArtifacts reads remote plugins from cache directory
The `BuildArtifacts` use case SHALL read remote plugin files from the plugin cache directory (resolved via `commit_sha` from lock entry) and copy them to platform output directories.

#### Scenario: Build with remote plugin
- **WHEN** `execute()` is called and the lock file contains a remote plugin entry with `commit_sha`
- **THEN** the builder reads files from `.promptkit/cache/plugins/{registry}/{plugin}/{sha}/`
- **AND** copies them to the platform output directory with appropriate directory mapping

#### Scenario: Build with local prompt (unchanged)
- **WHEN** the lock file contains a local prompt entry (no `commit_sha`)
- **THEN** the existing `Prompt`-based build path is used (read from `prompts/`, build from content)

#### Scenario: Plugin cache missing
- **WHEN** the lock file has a `commit_sha` but the cache directory doesn't exist
- **THEN** a `BuildError` is raised suggesting `promptkit lock` to re-fetch
