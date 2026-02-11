## ADDED Requirements

### Requirement: Plugin domain value object represents a fetched plugin manifest
The `Plugin` value object SHALL hold a spec, file list, source directory, and optional commit SHA. It does NOT hold file content — files stay on disk. Works for both local and registry plugins.

#### Scenario: Plugin created from registry fetch
- **GIVEN** a fetcher downloads a plugin with 3 files to cache
- **WHEN** a `Plugin` is constructed with spec, files, source_dir, and commit_sha
- **THEN** `plugin.spec` returns the PromptSpec
- **AND** `plugin.files` returns a tuple of relative paths (e.g., `("agents/reviewer.md", "hooks/hooks.json", "scripts/check.sh")`)
- **AND** `plugin.source_dir` returns the cache directory path
- **AND** `plugin.commit_sha` returns the commit SHA string

#### Scenario: Plugin created from local fetch
- **GIVEN** a local plugin directory exists in `prompts/my-skill/`
- **WHEN** a `Plugin` is constructed with spec, files, source_dir, and no commit_sha
- **THEN** `plugin.source_dir` returns the prompts directory path
- **AND** `plugin.commit_sha` is `None`

### Requirement: PluginFetcher protocol for fetching plugins
The `PluginFetcher` protocol SHALL define `fetch(spec) -> Plugin` which resolves plugin files and returns a `Plugin` manifest. `cache_dir` and other configuration are injected at construction time. Both `LocalPluginFetcher` and `ClaudeMarketplaceFetcher` implement this.

#### Scenario: Fetcher returns plugin manifest
- **WHEN** `fetch(spec)` is called
- **THEN** a `Plugin` manifest is returned with the spec, file list, source dir, and optional commit SHA

### Requirement: LocalPluginFetcher discovers and fetches local plugins
The `LocalPluginFetcher` SHALL scan `prompts/` for local plugins (single `.md` files and directories with any file types) and return `Plugin` manifests. Files stay in `prompts/` — they are not copied to cache.

#### Scenario: Discover single .md file
- **WHEN** `discover()` is called and `prompts/` contains `my-rule.md`
- **THEN** a `PromptSpec(source="local/my-rule")` is returned

#### Scenario: Discover directory plugin
- **WHEN** `discover()` is called and `prompts/` contains `my-skill/` directory with `SKILL.md` and `scripts/check.sh`
- **THEN** a `PromptSpec(source="local/my-skill")` is returned

#### Scenario: Fetch single .md file
- **WHEN** `fetch(spec)` is called with `spec.source = "local/my-rule"`
- **THEN** `Plugin(spec, files=("my-rule.md",), source_dir=prompts/)` is returned

#### Scenario: Fetch directory plugin
- **WHEN** `fetch(spec)` is called with `spec.source = "local/my-skill"`
- **AND** `prompts/my-skill/` contains `SKILL.md` and `scripts/check.sh`
- **THEN** `Plugin(spec, files=("my-skill/SKILL.md", "my-skill/scripts/check.sh"), source_dir=prompts/)` is returned

#### Scenario: Discover nested category structure
- **WHEN** `discover()` is called and `prompts/` contains `rules/my-rule.md` and `skills/my-skill/SKILL.md`
- **THEN** specs are returned for each: `local/rules/my-rule` and `local/skills/my-skill`

### Requirement: ClaudeMarketplaceFetcher reads marketplace.json to resolve plugin paths
The `ClaudeMarketplaceFetcher` SHALL read `marketplace.json` from the local git clone directory at `.promptkit/registries/{registry_name}/.claude-plugin/marketplace.json` using filesystem reads. It SHALL NOT use the GitHub Contents API.

#### Scenario: Plugin found in marketplace.json with relative path source
- **WHEN** `fetch(spec)` is called with `spec.prompt_name` equal to `"code-simplifier"`
- **AND** the local clone contains `.claude-plugin/marketplace.json` with an entry `"name": "code-simplifier"` and `"source": "./plugins/code-simplifier"`
- **THEN** the fetcher resolves the plugin source path to `plugins/code-simplifier`

#### Scenario: Plugin not found in marketplace.json
- **WHEN** `fetch(spec)` is called with a prompt name that does not match any entry
- **THEN** a `SyncError` is raised with a message indicating the plugin was not found

#### Scenario: Plugin has external git URL source (skipped for MVP)
- **WHEN** `marketplace.json` contains an entry with `"source": {"source": "url", "url": "https://..."}`
- **AND** `fetch(spec)` is called for that plugin
- **THEN** a `SyncError` is raised indicating external sources are not yet supported

#### Scenario: marketplace.json not found in clone
- **WHEN** the local clone does not contain `.claude-plugin/marketplace.json`
- **THEN** a `SyncError` is raised with a message describing the missing manifest

### Requirement: ClaudeMarketplaceFetcher downloads ALL files in plugin directory
The fetcher SHALL copy all files from the plugin directory in the local git clone to the cache directory, instead of downloading via GitHub Contents API. It SHALL preserve relative directory structure.

#### Scenario: Plugin with mixed file types
- **WHEN** the plugin directory in the clone contains `agents/reviewer.md`, `.claude-plugin/plugin.json`, `hooks/hooks.json`, `scripts/check.sh`
- **THEN** all 4 files are copied to the cache directory preserving their relative paths
- **AND** the returned `Plugin.files` lists all 4 relative paths

#### Scenario: Plugin directory not found in clone
- **WHEN** the resolved plugin source path does not exist in the local clone
- **THEN** a `SyncError` is raised

### Requirement: ClaudeMarketplaceFetcher handles skills repo structure
The fetcher SHALL support the skills repo structure by copying skill directories from the local clone instead of downloading via GitHub Contents API.

#### Scenario: Plugin with skills array
- **WHEN** `marketplace.json` contains an entry with `"source": "./"` and `"skills": ["./skills/xlsx", "./skills/docx"]`
- **THEN** the fetcher copies all files from each listed skill directory in the clone
- **AND** the `Plugin.files` includes paths like `skills/xlsx/SKILL.md`, `skills/xlsx/scripts/processor.py`, `skills/docx/SKILL.md`

### Requirement: ClaudeMarketplaceFetcher retrieves commit SHA for cache key
The fetcher SHALL get the commit SHA from the local git clone using `GitRegistryClone.get_commit_sha()` instead of the GitHub Commits API.

#### Scenario: Commit SHA retrieved from local clone
- **WHEN** the fetcher queries the local clone for the HEAD commit
- **THEN** the commit SHA from `git rev-parse HEAD` is used as part of the cache path `{registry}/{plugin}/{sha}/`
- **AND** the returned `Plugin.commit_sha` matches

### Requirement: ClaudeMarketplaceFetcher parses GitHub repository URL
The fetcher SHALL extract `owner` and `repo` from the registry URL to construct the git clone URL.

#### Scenario: Standard GitHub URL
- **WHEN** constructed with `registry_url="https://github.com/anthropics/claude-plugins-official"`
- **THEN** the clone URL is `https://github.com/anthropics/claude-plugins-official.git`

#### Scenario: Invalid URL format
- **WHEN** constructed with a URL that does not match `https://github.com/{owner}/{repo}`
- **THEN** a `SyncError` is raised at construction time

### Requirement: ClaudeMarketplaceFetcher ensures clone is up to date before fetching
The fetcher SHALL call `GitRegistryClone.ensure_up_to_date()` before reading any files from the clone, ensuring the local clone reflects the latest remote state.

#### Scenario: First fetch triggers clone
- **WHEN** `fetch(spec)` is called and no local clone exists
- **THEN** `GitRegistryClone.ensure_up_to_date()` clones the repository before proceeding

#### Scenario: Subsequent fetch triggers pull
- **WHEN** `fetch(spec)` is called and a local clone already exists
- **THEN** `GitRegistryClone.ensure_up_to_date()` pulls the latest changes before proceeding

### Requirement: ClaudeMarketplaceFetcher accepts injectable GitRegistryClone
The fetcher SHALL accept a `GitRegistryClone` parameter for testability, replacing the previous `httpx.Client` injection.

#### Scenario: Custom clone provided
- **WHEN** constructed with `clone=mock_clone`
- **THEN** all git operations use the provided clone object

### Requirement: PluginCache manages directory-based plugin storage
The `PluginCache` SHALL provide methods to check if a plugin version is cached, get the cache path for a plugin version, and list cached files.

#### Scenario: Plugin not yet cached
- **WHEN** `has(registry, plugin, sha)` is called and no matching directory exists
- **THEN** returns `False`

#### Scenario: Plugin already cached
- **WHEN** `has(registry, plugin, sha)` is called and the directory exists
- **THEN** returns `True`

#### Scenario: Get cache path
- **WHEN** `plugin_dir(registry, plugin, sha)` is called
- **THEN** returns `Path` to `.promptkit/cache/plugins/{registry}/{plugin}/{sha}/`

### Requirement: ArtifactBuilder copies file trees to platform output
Builders SHALL receive source directories and copy file trees to platform output directories with directory mapping.

#### Scenario: Build for Claude Code
- **WHEN** building a plugin with files `agents/reviewer.md`, `skills/my-skill/SKILL.md`, `hooks/hooks.json`
- **THEN** all files are copied to `.claude/` preserving directory structure

#### Scenario: Build for Cursor
- **WHEN** building a plugin with files `agents/reviewer.md`, `skills/my-skill/SKILL.md`
- **THEN** only skills are copied to `.cursor/` (agents, commands, hooks are skipped for Cursor)
- **AND** skills directory is preserved as `skills/`
