## ADDED Requirements

### Requirement: CodexBuilder copies only skills category files
The `CodexBuilder` SHALL implement the `ArtifactBuilder` protocol and copy only files under the `skills/` category directory to `.codex/`. Files outside the `skills/` category (e.g., `commands/`, `agents/`, `rules/`, `README.md`) SHALL be skipped. Directory structure within `skills/` is preserved as-is.

#### Scenario: Copy files in skills category
- **WHEN** a plugin contains files in `skills/my-skill/SKILL.md` and `skills/another/SKILL.md`
- **THEN** all files under `skills/` are copied to the output directory preserving structure

#### Scenario: Skip files outside skills category
- **WHEN** a plugin contains files in `commands/foo.md`, `agents/bar.md`, `rules/baz.md`
- **THEN** those files are not copied to the output directory

#### Scenario: Skip flat files with no category
- **WHEN** a plugin file has no directory prefix (e.g., `README.md`)
- **THEN** the file is not copied to the output directory

### Requirement: CodexBuilder copies content without transformation
The `CodexBuilder` SHALL write prompt content as-is, with no content transformation or frontmatter stripping.

#### Scenario: Content is preserved exactly
- **WHEN** a prompt with content including frontmatter is built
- **THEN** the output file contains the exact same content as the input

### Requirement: CodexBuilder cleans output directory before writing
The `CodexBuilder` SHALL remove only previously promptkit-managed files (listed in `.promptkit/managed/codex.txt`) before writing new artifacts, instead of removing the entire output directory. Non-managed files SHALL be preserved.

#### Scenario: Stale artifacts are removed, non-managed files preserved
- **WHEN** the output directory contains artifacts from a previous build listed in `.promptkit/managed/codex.txt`
- **AND** the output directory contains non-managed files (e.g., `skills/user-custom/SKILL.md`)
- **AND** the builder writes new artifacts
- **THEN** the previous managed artifacts are removed
- **AND** the non-managed files are preserved
- **AND** only the new artifacts and non-managed files exist in the output directory

### Requirement: CodexBuilder reports its platform
The `CodexBuilder` SHALL expose `PlatformTarget.CODEX` as its platform.

#### Scenario: Platform property returns codex
- **WHEN** the builder's `platform` property is accessed
- **THEN** `PlatformTarget.CODEX` is returned

### Requirement: CodexBuilder returns generated artifact paths
The `CodexBuilder` SHALL return a list of paths to all generated artifact files.

#### Scenario: Build returns paths of written files
- **WHEN** the builder writes artifacts for two plugins each with a skill
- **THEN** a list of two `Path` objects is returned, each pointing to a generated file

### Requirement: CodexBuilder uses FileSystem protocol
The `CodexBuilder` SHALL depend on the `FileSystem` protocol for all file operations.

#### Scenario: Builder operates through FileSystem
- **WHEN** `CodexBuilder` is constructed
- **THEN** it accepts a `FileSystem` instance
- **AND** all file operations go through the `FileSystem` protocol

### Requirement: PlatformTarget includes CODEX member
The `PlatformTarget` enum SHALL include a `CODEX` member with string value `"codex"`.

#### Scenario: CODEX enum member exists
- **WHEN** `PlatformTarget.CODEX` is accessed
- **THEN** its value is `"codex"`

#### Scenario: from_string resolves codex
- **WHEN** `PlatformTarget.from_string("codex")` is called
- **THEN** `PlatformTarget.CODEX` is returned

### Requirement: YAML config loader recognizes codex platform
The YAML config loader SHALL accept `codex` as a valid platform key under `platforms:` and resolve it to `PlatformTarget.CODEX`. The default output directory for Codex SHALL be `.codex`.

#### Scenario: Codex platform in config with default output dir
- **WHEN** `promptkit.yaml` contains `platforms: { codex: }` with no explicit output dir
- **THEN** the loader produces a `PlatformConfig` with `platform_type=PlatformTarget.CODEX` and `output_dir=".codex"`

#### Scenario: Codex platform with custom output dir
- **WHEN** `promptkit.yaml` contains `platforms: { codex: .my-codex }`
- **THEN** the loader produces a `PlatformConfig` with `output_dir=".my-codex"`

#### Scenario: Codex is not a default platform
- **WHEN** `promptkit.yaml` has no `platforms:` key
- **THEN** the default platform configs include Cursor and Claude Code but NOT Codex

### Requirement: CLI registers CodexBuilder
The CLI composition root SHALL register `CodexBuilder` in the builders mapping keyed by `PlatformTarget.CODEX`.

#### Scenario: CodexBuilder is wired in CLI
- **WHEN** `_make_build_use_case()` is called
- **THEN** the returned `BuildArtifacts` instance has a builder for `PlatformTarget.CODEX`
