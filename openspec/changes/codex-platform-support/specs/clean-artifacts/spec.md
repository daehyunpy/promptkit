## MODIFIED Requirements

### Requirement: Clean use case removes all managed build artifacts
The `CleanArtifacts` use case SHALL discover all platform manifests in `.promptkit/managed/`, read each manifest, remove the listed files from their respective output directories, prune empty parent directories, and delete the manifest files.

#### Scenario: Clean with existing manifests for all platforms
- **WHEN** `.promptkit/managed/cursor.txt` lists `skills/foo.md`, `.promptkit/managed/claude.txt` lists `skills/bar.md`, and `.promptkit/managed/codex.txt` lists `skills/baz/SKILL.md`
- **THEN** `skills/foo.md` is removed from `.cursor/`, `skills/bar.md` is removed from `.claude/`, `skills/baz/SKILL.md` is removed from `.codex/`, all manifest files are deleted, and empty parent directories are pruned

### Requirement: Clean discovers platforms from manifest directory
The `CleanArtifacts` use case SHALL discover platforms by listing `*.txt` files in `.promptkit/managed/`, not by reading `promptkit.yaml`. The platform name SHALL be derived from the manifest filename (e.g., `codex.txt` → platform name `codex`).

#### Scenario: Codex manifest is discovered and cleaned
- **WHEN** `.promptkit/managed/codex.txt` exists listing `skills/my-skill/SKILL.md`
- **THEN** the use case maps platform name `codex` to output directory `.codex`
- **AND** removes `skills/my-skill/SKILL.md` from `.codex/`
- **AND** prunes empty parent directories
- **AND** deletes the manifest file
