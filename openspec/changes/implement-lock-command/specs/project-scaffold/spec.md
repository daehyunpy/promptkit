## MODIFIED Requirements

### Requirement: FileSystem protocol supports read operations
The `FileSystem` protocol SHALL include methods for reading files and listing directory contents, in addition to existing write operations.

#### Scenario: Read file content
- **WHEN** `read_file(path)` is called with a path to an existing file
- **THEN** the file content is returned as a string

#### Scenario: Read nonexistent file
- **WHEN** `read_file(path)` is called with a path to a file that does not exist
- **THEN** a `FileNotFoundError` is raised

#### Scenario: List directory contents
- **WHEN** `list_directory(path)` is called with a path to an existing directory
- **THEN** a list of `Path` objects for the directory's immediate children is returned

#### Scenario: List nonexistent directory
- **WHEN** `list_directory(path)` is called with a path to a directory that does not exist
- **THEN** an empty list is returned
