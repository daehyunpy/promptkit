## ADDED Requirements

### Requirement: ClaudeBuilder routes prompts to Claude Code directories
The `ClaudeBuilder` SHALL implement the `ArtifactBuilder` protocol and write prompt content to `.claude/` subdirectories based on the prompt's source category. Claude Code preserves category names as-is.

#### Scenario: Route skills category to skills directory
- **WHEN** a prompt with source `local/skills/my-skill` is built
- **THEN** the output file is written to `<output_dir>/skills/my-skill.md`

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

### Requirement: ClaudeBuilder copies content without transformation
The `ClaudeBuilder` SHALL write prompt content as-is, with no content transformation or frontmatter stripping.

#### Scenario: Content is preserved exactly
- **WHEN** a prompt with content including frontmatter is built
- **THEN** the output file contains the exact same content as the input

### Requirement: ClaudeBuilder cleans output directory before writing
The `ClaudeBuilder` SHALL remove all existing artifacts from its output directory before writing new ones.

#### Scenario: Stale artifacts are removed
- **WHEN** the output directory contains artifacts from a previous build
- **AND** the builder writes new artifacts
- **THEN** the previous artifacts are removed
- **AND** only the new artifacts exist in the output directory

### Requirement: ClaudeBuilder reports its platform
The `ClaudeBuilder` SHALL expose `PlatformTarget.CLAUDE_CODE` as its platform.

#### Scenario: Platform property returns claude-code
- **WHEN** the builder's `platform` property is accessed
- **THEN** `PlatformTarget.CLAUDE_CODE` is returned

### Requirement: ClaudeBuilder returns generated artifact paths
The `ClaudeBuilder` SHALL return a list of paths to all generated artifact files.

#### Scenario: Build returns paths of written files
- **WHEN** the builder writes artifacts for three prompts
- **THEN** a list of three `Path` objects is returned, each pointing to a generated file

### Requirement: ClaudeBuilder uses FileSystem protocol
The `ClaudeBuilder` SHALL depend on the `FileSystem` protocol for all file operations.

#### Scenario: Builder operates through FileSystem
- **WHEN** `ClaudeBuilder` is constructed
- **THEN** it accepts a `FileSystem` instance
- **AND** all file operations go through the `FileSystem` protocol
