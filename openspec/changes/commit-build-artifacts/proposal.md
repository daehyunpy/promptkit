## Why

`promptkit build` generates `.cursor/` and `.claude/` artifacts, but both builders call `remove_directory(output_dir)` before writing — wiping the entire output directory. This destroys non-promptkit files that live alongside build outputs (e.g., `.claude/settings.json`, `.claude/skills/` from other tools like OpenSpec). Users who commit build artifacts to git (the recommended workflow for team standardization) lose existing platform configuration every time they rebuild.

Additionally, there is no guidance or mechanism protecting non-promptkit files in these shared directories. The build output should coexist with files managed by other tools.

## What Changes

- **Builders clean only promptkit-managed files** instead of wiping the entire output directory. Each builder tracks which subdirectories it manages (based on category routing) and only removes files within those scoped paths, preserving unrelated files like `settings.json`.
- **Builders write a manifest** (`.promptkit-managed`) listing generated file paths, so subsequent builds know exactly which files to clean without touching others.
- **`.gitignore` template updated** — `promptkit init` no longer suggests gitignoring `.cursor/` and `.claude/`, since committing build artifacts is the intended workflow for team collaboration.

## Capabilities

### New Capabilities
- `safe-build-output`: Builders perform scoped cleanup using a manifest of previously generated files instead of wiping the entire output directory

### Modified Capabilities
- `build-artifacts`: Build use case reads/writes a `.promptkit-managed` manifest per output directory to track generated files
- `claude-builder`: Scoped cleanup — removes only previously managed files, then writes new artifacts
- `cursor-builder`: Scoped cleanup — removes only previously managed files, then writes new artifacts

## Impact

- **Infrastructure layer**: `ClaudeBuilder` and `CursorBuilder` change from `remove_directory(output_dir)` to manifest-based scoped cleanup
- **Application layer**: `BuildArtifacts` may coordinate manifest read/write if not delegated to builders
- **Tests**: Builder tests need updating — current tests assert on clean-slate behavior; new tests verify non-managed files are preserved
- **Project scaffold**: `promptkit init` gitignore template changes
- **Existing users**: Build output directories are no longer wiped — **non-breaking** but behavior change
