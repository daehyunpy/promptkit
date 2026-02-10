## MODIFIED Requirements

### Requirement: BuildArtifacts delegates to platform builders
The `BuildArtifacts` use case SHALL delegate artifact generation to each configured platform builder. Builders are responsible for their own cleanup strategy (manifest-based scoped cleanup).

#### Scenario: Build for multiple platforms
- **WHEN** config defines both `cursor` and `claude-code` platforms
- **THEN** `CursorBuilder.build()` is called with cursor-targeted prompts
- **AND** `ClaudeBuilder.build()` is called with claude-code-targeted prompts
- **AND** each builder manages its own cleanup via `.promptkit-managed`

#### Scenario: Build for single platform
- **WHEN** config defines only `cursor` platform
- **THEN** only `CursorBuilder.build()` is called
