## MODIFIED Requirements

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

### REMOVED Requirements

### Requirement: Prompt aggregate and PromptFetcher protocol
The `Prompt` aggregate (content string in memory) and `PromptFetcher` protocol are removed. Replaced by `Plugin` (file tree on disk) and `PluginFetcher` protocol.

### Requirement: PromptCache (content-addressable)
The `PromptCache` (flat `sha256-*.md` files) is removed. Registry plugins use `PluginCache` (directory-based). Local plugins read from `prompts/` directly.
