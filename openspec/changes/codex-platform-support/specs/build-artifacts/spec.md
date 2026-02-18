## MODIFIED Requirements

### Requirement: BuildArtifacts filters prompts by platform
The `BuildArtifacts` use case SHALL filter prompts using `Prompt.is_valid_for_platform()` before delegating to each builder.

#### Scenario: Prompt targets specific platform
- **WHEN** a prompt targets only `cursor` platform
- **THEN** it is included in the `CursorBuilder` build
- **AND** it is excluded from the `ClaudeBuilder` and `CodexBuilder` builds

#### Scenario: Prompt targets all platforms
- **WHEN** a prompt has no platform restriction (empty platforms)
- **THEN** it is included in all configured platform builds including Codex

### Requirement: BuildArtifacts delegates to platform builders
The `BuildArtifacts` use case SHALL delegate artifact generation to each configured platform builder. Builders are responsible for their own cleanup strategy (manifest-based scoped cleanup).

#### Scenario: Build for multiple platforms including codex
- **WHEN** config defines `cursor`, `claude-code`, and `codex` platforms
- **THEN** `CursorBuilder.build()` is called with cursor-targeted prompts
- **AND** `ClaudeBuilder.build()` is called with claude-code-targeted prompts
- **AND** `CodexBuilder.build()` is called with codex-targeted prompts
- **AND** each builder manages its own cleanup via `.promptkit/managed/`

#### Scenario: Build skips unconfigured platform
- **WHEN** config defines only `cursor` and `claude-code` platforms (no `codex`)
- **THEN** `CodexBuilder.build()` is not called
