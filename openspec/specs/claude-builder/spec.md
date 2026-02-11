## ADDED Requirements

### Requirement: ClaudeBuilder copies only allowed category files
The `ClaudeBuilder` SHALL implement the `ArtifactBuilder` protocol and copy only files under allowed category directories to `.claude/`. The allowed categories are: `commands`, `agents`, `skills`, `hooks`, `scripts`, `rules`. Files outside these categories (e.g., `README.md`, `.claude-plugin/`) SHALL be skipped. Directory structure within allowed categories is preserved as-is.

#### Scenario: Copy files in allowed categories
- **WHEN** a plugin contains files in `commands/`, `agents/`, `skills/`, `hooks/`, `scripts/`, and `rules/`
- **THEN** all files under those directories are copied to the output directory

#### Scenario: Skip files outside allowed categories
- **WHEN** a plugin contains `README.md` and `.claude-plugin/plugin.json`
- **THEN** those files are not copied to the output directory

#### Scenario: Skip flat files with no category
- **WHEN** a plugin file has no directory prefix (e.g., `my-file.md`)
- **THEN** the file is not copied to the output directory

### Requirement: ClaudeBuilder copies content without transformation
The `ClaudeBuilder` SHALL write prompt content as-is, with no content transformation or frontmatter stripping.

#### Scenario: Content is preserved exactly
- **WHEN** a prompt with content including frontmatter is built
- **THEN** the output file contains the exact same content as the input

### Requirement: ClaudeBuilder cleans output directory before writing
The `ClaudeBuilder` SHALL remove only previously promptkit-managed files (listed in `.promptkit/managed/`) before writing new artifacts, instead of removing the entire output directory. Non-managed files SHALL be preserved.

#### Scenario: Stale artifacts are removed, non-managed files preserved
- **WHEN** the output directory contains artifacts from a previous build listed in `.promptkit/managed/`
- **AND** the output directory contains non-managed files (e.g., `settings.json`, `skills/openspec-apply/SKILL.md`)
- **AND** the builder writes new artifacts
- **THEN** the previous managed artifacts are removed
- **AND** the non-managed files are preserved
- **AND** only the new artifacts and non-managed files exist in the output directory

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
