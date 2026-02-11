## ADDED Requirements

### Requirement: BuildArtifacts requires a lock file
The `BuildArtifacts` use case SHALL require `promptkit.lock` to exist before building. It SHALL raise a `BuildError` if no lock file is found.

#### Scenario: Lock file missing
- **WHEN** `BuildArtifacts.execute()` is called
- **AND** `promptkit.lock` does not exist
- **THEN** a `BuildError` is raised with a message indicating the lock file is required

### Requirement: BuildArtifacts loads prompts from lock entries
The `BuildArtifacts` use case SHALL read each lock entry and load the prompt content from the cache (for remote prompts) or from the `prompts/` directory (for local prompts).

#### Scenario: Load local prompt content
- **WHEN** a lock entry has source `local/skills/my-skill`
- **THEN** the content is read from `prompts/skills/my-skill.md`

#### Scenario: Load cached remote prompt content
- **WHEN** a lock entry has source `registry/prompt-name` with content hash `sha256:<hex>`
- **THEN** the content is retrieved from the prompt cache using the content hash

#### Scenario: Missing cached content raises error
- **WHEN** a lock entry references a content hash not found in the cache
- **THEN** a `BuildError` is raised indicating the cached content is missing

### Requirement: BuildArtifacts filters prompts by platform
The `BuildArtifacts` use case SHALL filter prompts using `Prompt.is_valid_for_platform()` before delegating to each builder.

#### Scenario: Prompt targets specific platform
- **WHEN** a prompt targets only `cursor` platform
- **THEN** it is included in the `CursorBuilder` build
- **AND** it is excluded from the `ClaudeBuilder` build

#### Scenario: Prompt targets all platforms
- **WHEN** a prompt has no platform restriction (empty platforms)
- **THEN** it is included in both the `CursorBuilder` and `ClaudeBuilder` builds

### Requirement: BuildArtifacts delegates to platform builders
The `BuildArtifacts` use case SHALL delegate artifact generation to each configured platform builder. Builders are responsible for their own cleanup strategy (manifest-based scoped cleanup).

#### Scenario: Build for multiple platforms
- **WHEN** config defines both `cursor` and `claude-code` platforms
- **THEN** `CursorBuilder.build()` is called with cursor-targeted prompts
- **AND** `ClaudeBuilder.build()` is called with claude-code-targeted prompts
- **AND** each builder manages its own cleanup via `.promptkit/managed/`

#### Scenario: Build for single platform
- **WHEN** config defines only `cursor` platform
- **THEN** only `CursorBuilder.build()` is called

### Requirement: BuildArtifacts loads config for platform definitions
The `BuildArtifacts` use case SHALL load `promptkit.yaml` to determine which platforms to build for and their output directories.

#### Scenario: Config loaded successfully
- **WHEN** `BuildArtifacts.execute()` is called
- **THEN** `promptkit.yaml` is parsed to obtain platform configurations

#### Scenario: Config missing
- **WHEN** `promptkit.yaml` does not exist
- **THEN** a `FileNotFoundError` propagates
