## ADDED Requirements

### Requirement: Clean use case removes all managed build artifacts
The `CleanArtifacts` use case SHALL discover all platform manifests in `.promptkit/managed/`, read each manifest, remove the listed files from their respective output directories, prune empty parent directories, and delete the manifest files.

#### Scenario: Clean with existing manifests for both platforms
- **WHEN** `.promptkit/managed/cursor.txt` lists `skills/foo.md` and `.promptkit/managed/claude.txt` lists `skills/bar.md`
- **THEN** `skills/foo.md` is removed from `.cursor/`, `skills/bar.md` is removed from `.claude/`, both manifest files are deleted, and empty parent directories are pruned

#### Scenario: Clean with no manifests present
- **WHEN** `.promptkit/managed/` directory does not exist or contains no manifest files
- **THEN** clean completes successfully with no files removed (no-op)

#### Scenario: Clean preserves non-managed files
- **WHEN** `.cursor/` contains both managed file `skills/foo.md` and non-managed file `settings.json`
- **THEN** only `skills/foo.md` is removed; `settings.json` is untouched

#### Scenario: Clean handles already-deleted managed files
- **WHEN** manifest lists `skills/foo.md` but the file has already been manually deleted
- **THEN** clean completes successfully, skipping the missing file

### Requirement: Clean use case optionally removes plugin cache
The `CleanArtifacts` use case SHALL accept a `clean_cache` flag. When true, it SHALL remove the entire `.promptkit/cache/` directory tree after cleaning build artifacts.

#### Scenario: Clean with cache flag removes cache directory
- **WHEN** `clean_cache` is true and `.promptkit/cache/` exists with cached plugins
- **THEN** the entire `.promptkit/cache/` directory tree is removed

#### Scenario: Clean without cache flag preserves cache
- **WHEN** `clean_cache` is false (default)
- **THEN** `.promptkit/cache/` is not modified

#### Scenario: Clean with cache flag when cache doesn't exist
- **WHEN** `clean_cache` is true but `.promptkit/cache/` does not exist
- **THEN** clean completes successfully (no error)

### Requirement: Clean discovers platforms from manifest directory
The `CleanArtifacts` use case SHALL discover platforms by listing `*.txt` files in `.promptkit/managed/`, not by reading `promptkit.yaml`. The platform name SHALL be derived from the manifest filename (e.g., `cursor.txt` → platform name `cursor`).

#### Scenario: Config file is missing but manifests exist
- **WHEN** `promptkit.yaml` does not exist but `.promptkit/managed/cursor.txt` exists
- **THEN** clean successfully removes managed cursor artifacts without requiring config

#### Scenario: Platform output directory derived from manifest
- **WHEN** manifest file is `cursor.txt`
- **THEN** the use case reads the platform output directory mapping to determine where managed files live
