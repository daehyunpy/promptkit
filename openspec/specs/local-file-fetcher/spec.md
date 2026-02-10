## ADDED Requirements

### Requirement: LocalFileFetcher implements PromptFetcher protocol
The `LocalFileFetcher` SHALL implement the `PromptFetcher` protocol to fetch prompts from the local `prompts/` directory.

#### Scenario: Fetch local prompt by spec
- **WHEN** `fetch(spec)` is called with a `PromptSpec` whose source is `local/my-rule`
- **THEN** the content of `prompts/my-rule.md` is read
- **AND** a `Prompt` is returned with the file content and the given spec

#### Scenario: Fetch local prompt from subdirectory
- **WHEN** `fetch(spec)` is called with a `PromptSpec` whose source is `local/skills/my-skill`
- **THEN** the content of `prompts/skills/my-skill.md` is read
- **AND** a `Prompt` is returned with the file content

#### Scenario: Fetch nonexistent local prompt
- **WHEN** `fetch(spec)` is called with a `PromptSpec` whose source references a file that does not exist
- **THEN** a `SyncError` is raised with a message indicating the missing file

### Requirement: LocalFileFetcher discovers local prompts
The `LocalFileFetcher` SHALL discover all `.md` files in the `prompts/` directory and return `PromptSpec` objects for each.

#### Scenario: Discover prompts in flat directory
- **WHEN** `discover()` is called and `prompts/` contains `my-rule.md` and `my-helper.md`
- **THEN** a list of two `PromptSpec` objects is returned
- **AND** each has source format `local/<filename-without-extension>` (e.g., `local/my-rule`)

#### Scenario: Discover prompts in subdirectories
- **WHEN** `discover()` is called and `prompts/skills/code-review.md` exists
- **THEN** a `PromptSpec` with source `local/skills/code-review` is returned

#### Scenario: Empty prompts directory
- **WHEN** `discover()` is called and `prompts/` is empty or does not exist
- **THEN** an empty list is returned

#### Scenario: Non-markdown files are ignored
- **WHEN** `discover()` is called and `prompts/` contains `notes.txt` and `config.yaml`
- **THEN** those files are not included in the returned list

### Requirement: LocalFileFetcher uses FileSystem protocol
The `LocalFileFetcher` SHALL depend on the `FileSystem` protocol for all file operations.

#### Scenario: Constructor accepts FileSystem and prompts directory
- **WHEN** `LocalFileFetcher` is constructed
- **THEN** it accepts a `FileSystem` instance and a `Path` for the prompts directory
