## MODIFIED Requirements

### Requirement: CursorBuilder cleans output directory before writing
The `CursorBuilder` SHALL remove only previously promptkit-managed files (listed in `.promptkit/managed/`) before writing new artifacts, instead of removing the entire output directory. Non-managed files SHALL be preserved.

#### Scenario: Stale artifacts are removed, non-managed files preserved
- **WHEN** the output directory contains artifacts from a previous build listed in `.promptkit/managed/`
- **AND** the output directory contains non-managed files (e.g., `settings.json`)
- **AND** the builder writes new artifacts
- **THEN** the previous managed artifacts are removed
- **AND** the non-managed files are preserved
- **AND** only the new artifacts and non-managed files exist in the output directory
