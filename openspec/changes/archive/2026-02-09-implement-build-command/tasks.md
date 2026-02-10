## 1. Category Extraction Helper

- [x] 1.1 Add `category` property to `Prompt` that extracts the source category from the source path (e.g., `local/skills/my-skill` → `skills`, `local/my-rule` → `rules` default)
- [x] 1.2 Write tests for category extraction covering all categories (skills, rules, agents, commands, subagents) and the flat-source default

## 2. CursorBuilder

- [x] 2.1 Create `source/promptkit/infra/builders/cursor_builder.py` implementing `ArtifactBuilder` protocol with `CATEGORY_DIRS` mapping and `FileSystem` dependency
- [x] 2.2 Write tests for CursorBuilder: routes each category to correct output subdirectory (skills → skills-cursor, rules → rules, agents → agents, commands → commands, subagents → subagents)
- [x] 2.3 Write test for CursorBuilder: flat source defaults to rules directory
- [x] 2.4 Write test for CursorBuilder: content is copied without transformation
- [x] 2.5 Write test for CursorBuilder: cleans output directory before writing
- [x] 2.6 Write test for CursorBuilder: returns list of generated paths
- [x] 2.7 Write test for CursorBuilder: platform property returns PlatformTarget.CURSOR

## 3. ClaudeBuilder

- [x] 3.1 Create `source/promptkit/infra/builders/claude_builder.py` implementing `ArtifactBuilder` protocol with `CATEGORY_DIRS` mapping and `FileSystem` dependency
- [x] 3.2 Write tests for ClaudeBuilder: routes each category to correct output subdirectory (all categories preserve names as-is)
- [x] 3.3 Write test for ClaudeBuilder: flat source defaults to rules directory
- [x] 3.4 Write test for ClaudeBuilder: content is copied without transformation
- [x] 3.5 Write test for ClaudeBuilder: cleans output directory before writing
- [x] 3.6 Write test for ClaudeBuilder: returns list of generated paths
- [x] 3.7 Write test for ClaudeBuilder: platform property returns PlatformTarget.CLAUDE_CODE

## 4. BuildArtifacts Use Case

- [x] 4.1 Create `source/promptkit/app/build.py` with `BuildArtifacts` class that loads config, lock, reads prompts, filters by platform, and delegates to builders
- [x] 4.2 Write test: raises BuildError when lock file is missing
- [x] 4.3 Write test: loads local prompt content from prompts/ directory via source path
- [x] 4.4 Write test: loads cached remote prompt content via content hash
- [x] 4.5 Write test: raises BuildError when cached content is missing
- [x] 4.6 Write test: filters prompts by platform before delegating to builders
- [x] 4.7 Write test: delegates to each configured platform builder
- [x] 4.8 Write test: builds for single platform when only one configured

## 5. CLI Build Command

- [x] 5.1 Add `build` command to `cli.py` that wires up `BuildArtifacts` with real infrastructure
- [x] 5.2 Write test: successful build prints success message
- [x] 5.3 Write test: missing lock file prints error and exits with code 1
- [x] 5.4 Write test: missing config prints error and exits with code 1
