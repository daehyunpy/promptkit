## ADDED Requirements

### Requirement: Cache stores content by SHA256 hash
The `PromptCache` SHALL store prompt content in `.promptkit/cache/` using content-addressable filenames of the form `sha256-<hex>.md`.

#### Scenario: Store new content
- **WHEN** `store("# My Prompt\nContent here")` is called
- **THEN** a file named `sha256-<hex>.md` is created in the cache directory where `<hex>` is the SHA256 hex digest of the content
- **AND** the method returns the full content hash string `sha256:<hex>`

#### Scenario: Store duplicate content
- **WHEN** `store()` is called with content that already exists in cache
- **THEN** the existing file is not modified
- **AND** the same content hash is returned

### Requirement: Cache retrieves content by hash
The `PromptCache` SHALL retrieve stored content given a content hash.

#### Scenario: Retrieve existing content
- **WHEN** `retrieve("sha256:<hex>")` is called for content that was previously stored
- **THEN** the original content string is returned

#### Scenario: Retrieve missing content
- **WHEN** `retrieve("sha256:<hex>")` is called for a hash not in the cache
- **THEN** `None` is returned

### Requirement: Cache checks content existence
The `PromptCache` SHALL report whether content with a given hash exists.

#### Scenario: Check existing hash
- **WHEN** `has("sha256:<hex>")` is called for stored content
- **THEN** `True` is returned

#### Scenario: Check missing hash
- **WHEN** `has("sha256:<hex>")` is called for a hash not in the cache
- **THEN** `False` is returned

### Requirement: Cache uses FileSystem protocol
The `PromptCache` SHALL depend on the `FileSystem` protocol, not on direct file I/O, to enable testing.

#### Scenario: Cache operates through FileSystem
- **WHEN** `PromptCache` is constructed
- **THEN** it accepts a `FileSystem` instance and a `Path` for the cache directory
- **AND** all file operations go through the `FileSystem` protocol
