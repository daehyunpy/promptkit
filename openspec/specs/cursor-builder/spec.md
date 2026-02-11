## ADDED Requirements

### Requirement: CursorBuilder routes prompts to Cursor-specific directories
The `CursorBuilder` SHALL implement the `ArtifactBuilder` protocol and write prompt content to `.cursor/` subdirectories based on the prompt's source category.

#### Scenario: Route skills category to skills-cursor directory
- **WHEN** a prompt with source `local/skills/my-skill` is built
- **THEN** the output file is written to `<output_dir>/skills-cursor/my-skill.md`

#### Scenario: Route rules category to rules directory
- **WHEN** a prompt with source `local/rules/my-rule` is built
- **THEN** the output file is written to `<output_dir>/rules/my-rule.md`

#### Scenario: Route agents category to agents directory
- **WHEN** a prompt with source `local/agents/my-agent` is built
- **THEN** the output file is written to `<output_dir>/agents/my-agent.md`

#### Scenario: Route commands category to commands directory
- **WHEN** a prompt with source `local/commands/my-command` is built
- **THEN** the output file is written to `<output_dir>/commands/my-command.md`

#### Scenario: Route subagents category to subagents directory
- **WHEN** a prompt with source `local/subagents/my-subagent` is built
- **THEN** the output file is written to `<output_dir>/subagents/my-subagent.md`

#### Scenario: Default flat prompts to rules category
- **WHEN** a prompt with source `local/my-rule` (no subdirectory) is built
- **THEN** the output file is written to `<output_dir>/rules/my-rule.md`

### Requirement: CursorBuilder copies content without transformation
The `CursorBuilder` SHALL write prompt content as-is, with no content transformation or frontmatter stripping.

#### Scenario: Content is preserved exactly
- **WHEN** a prompt with content including frontmatter is built
- **THEN** the output file contains the exact same content as the input

### Requirement: CursorBuilder cleans output directory before writing
The `CursorBuilder` SHALL remove only previously promptkit-managed files (listed in `.promptkit/managed/`) before writing new artifacts, instead of removing the entire output directory. Non-managed files SHALL be preserved.

#### Scenario: Stale artifacts are removed, non-managed files preserved
- **WHEN** the output directory contains artifacts from a previous build listed in `.promptkit/managed/`
- **AND** the output directory contains non-managed files (e.g., `settings.json`)
- **AND** the builder writes new artifacts
- **THEN** the previous managed artifacts are removed
- **AND** the non-managed files are preserved
- **AND** only the new artifacts and non-managed files exist in the output directory

### Requirement: CursorBuilder reports its platform
The `CursorBuilder` SHALL expose `PlatformTarget.CURSOR` as its platform.

#### Scenario: Platform property returns cursor
- **WHEN** the builder's `platform` property is accessed
- **THEN** `PlatformTarget.CURSOR` is returned

### Requirement: CursorBuilder returns generated artifact paths
The `CursorBuilder` SHALL return a list of paths to all generated artifact files.

#### Scenario: Build returns paths of written files
- **WHEN** the builder writes artifacts for three prompts
- **THEN** a list of three `Path` objects is returned, each pointing to a generated file

### Requirement: CursorBuilder uses FileSystem protocol
The `CursorBuilder` SHALL depend on the `FileSystem` protocol for all file operations.

#### Scenario: Builder operates through FileSystem
- **WHEN** `CursorBuilder` is constructed
- **THEN** it accepts a `FileSystem` instance
- **AND** all file operations go through the `FileSystem` protocol
