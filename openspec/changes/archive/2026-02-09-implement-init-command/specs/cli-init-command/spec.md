## ADDED Requirements

### Requirement: CLI command is invocable via promptkit init
The system SHALL provide a `promptkit init` CLI command that can be invoked from the terminal.

#### Scenario: Command is available after installation
- **WHEN** user runs `promptkit --help`
- **THEN** `init` command is listed as an available command

#### Scenario: Command executes without arguments
- **WHEN** user runs `promptkit init` in an empty directory
- **THEN** the command executes and scaffolds the project structure

#### Scenario: Command shows help text
- **WHEN** user runs `promptkit init --help`
- **THEN** help text describing the command is displayed

### Requirement: Required directories are created
The system SHALL create all required promptkit directories in the current working directory.

#### Scenario: Cache directory is created
- **WHEN** user runs `promptkit init`
- **THEN** `.promptkit/cache/` directory exists

#### Scenario: Agents directory is created
- **WHEN** user runs `promptkit init`
- **THEN** `.agents/` directory exists

#### Scenario: Cursor output directory is created
- **WHEN** user runs `promptkit init`
- **THEN** `.cursor/` directory exists

#### Scenario: Claude Code output directory is created
- **WHEN** user runs `promptkit init`
- **THEN** `.claude/` directory exists

### Requirement: Configuration file is generated
The system SHALL generate a `promptkit.yaml` file with valid configuration structure.

#### Scenario: promptkit.yaml is created
- **WHEN** user runs `promptkit init`
- **THEN** `promptkit.yaml` file exists in the current directory

#### Scenario: Generated config is valid YAML
- **WHEN** user runs `promptkit init`
- **THEN** `promptkit.yaml` contains valid YAML that can be parsed

#### Scenario: Generated config has required fields
- **WHEN** examining the generated `promptkit.yaml`
- **THEN** it contains `version`, `prompts`, and `platforms` fields

#### Scenario: Generated config includes example prompt entry
- **WHEN** examining the generated `promptkit.yaml`
- **THEN** it contains a commented example prompt entry showing the structure

#### Scenario: Platform output directories are specified
- **WHEN** examining the generated `promptkit.yaml`
- **THEN** it specifies `output_dir` for both `cursor` and `claude-code` platforms

### Requirement: Lock file is created
The system SHALL generate an empty `promptkit.lock` file.

#### Scenario: promptkit.lock is created
- **WHEN** user runs `promptkit init`
- **THEN** `promptkit.lock` file exists in the current directory

#### Scenario: Lock file is valid YAML
- **WHEN** examining `promptkit.lock`
- **THEN** it contains valid YAML structure (even if empty)

### Requirement: Gitignore entries are added
The system SHALL add promptkit-specific entries to `.gitignore`.

#### Scenario: Gitignore is created if it does not exist
- **WHEN** user runs `promptkit init` in directory without `.gitignore`
- **THEN** `.gitignore` file is created with promptkit entries

#### Scenario: Gitignore entries are appended if file exists
- **WHEN** user runs `promptkit init` in directory with existing `.gitignore`
- **THEN** promptkit entries are appended to the existing file

#### Scenario: Cache directory is gitignored
- **WHEN** examining `.gitignore` after init
- **THEN** it contains `.promptkit/cache/` entry

### Requirement: Existing projects are not overwritten
The system SHALL refuse to initialize if `promptkit.yaml` already exists.

#### Scenario: Init fails when promptkit.yaml exists
- **WHEN** user runs `promptkit init` in directory with existing `promptkit.yaml`
- **THEN** the command exits with error code 1

#### Scenario: Error message guides user
- **WHEN** user runs `promptkit init` in directory with existing `promptkit.yaml`
- **THEN** an error message is displayed explaining that the project is already initialized

#### Scenario: No files are modified when init fails
- **WHEN** user runs `promptkit init` in directory with existing `promptkit.yaml`
- **THEN** no files or directories are created or modified

### Requirement: Success message provides guidance
The system SHALL display a success message with next steps after successful initialization.

#### Scenario: Success message is displayed
- **WHEN** user runs `promptkit init` successfully
- **THEN** a success message is printed to the terminal

#### Scenario: Next steps are shown
- **WHEN** examining the success message
- **THEN** it includes instructions for the next steps (edit config, run sync, run build)

#### Scenario: Created files are listed
- **WHEN** examining the success message
- **THEN** it lists all files and directories that were created

### Requirement: Command exits with appropriate status codes
The system SHALL exit with status code 0 on success and non-zero on failure.

#### Scenario: Success returns exit code 0
- **WHEN** user runs `promptkit init` successfully
- **THEN** the command exits with status code 0

#### Scenario: Failure returns non-zero exit code
- **WHEN** `promptkit init` encounters an error (e.g., existing promptkit.yaml)
- **THEN** the command exits with status code 1

### Requirement: Init works in any directory
The system SHALL be able to initialize a promptkit project in any writable directory.

#### Scenario: Init in empty directory succeeds
- **WHEN** user runs `promptkit init` in an empty directory
- **THEN** initialization completes successfully

#### Scenario: Init in directory with other files succeeds
- **WHEN** user runs `promptkit init` in directory with unrelated files
- **THEN** initialization completes successfully without affecting existing files

#### Scenario: Init respects current working directory
- **WHEN** user runs `promptkit init` from any location
- **THEN** files and directories are created in the current working directory, not elsewhere

### Requirement: Generated config is immediately usable
The system SHALL generate a `promptkit.yaml` that is valid and can be used immediately.

#### Scenario: Config can be validated
- **WHEN** user runs `promptkit validate` after `promptkit init`
- **THEN** validation passes (even with empty prompts list)

#### Scenario: Config structure matches schema
- **WHEN** examining the generated `promptkit.yaml`
- **THEN** its structure matches the expected schema defined in technical design
