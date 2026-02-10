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
The `PluginFetcher` protocol SHALL define `fetch(spec, cache_dir) -> Plugin` which resolves plugin files and returns a `Plugin` manifest. Both `LocalPluginFetcher` and `ClaudeMarketplaceFetcher` implement this.

#### Scenario: Fetcher returns plugin manifest
- **WHEN** `fetch(spec, cache_dir)` is called
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
- **WHEN** `fetch(spec, cache_dir)` is called with `spec.source = "local/my-rule"`
- **THEN** `Plugin(spec, files=("my-rule.md",), source_dir=prompts/)` is returned

#### Scenario: Fetch directory plugin
- **WHEN** `fetch(spec, cache_dir)` is called with `spec.source = "local/my-skill"`
- **AND** `prompts/my-skill/` contains `SKILL.md` and `scripts/check.sh`
- **THEN** `Plugin(spec, files=("my-skill/SKILL.md", "my-skill/scripts/check.sh"), source_dir=prompts/)` is returned

#### Scenario: Discover nested category structure
- **WHEN** `discover()` is called and `prompts/` contains `rules/my-rule.md` and `skills/my-skill/SKILL.md`
- **THEN** specs are returned for each: `local/rules/my-rule` and `local/skills/my-skill`

### Requirement: ClaudeMarketplaceFetcher reads marketplace.json to resolve plugin paths
The `ClaudeMarketplaceFetcher` SHALL fetch `.claude-plugin/marketplace.json` from the registry repository and use it to resolve the plugin's source path within the repo.

#### Scenario: Plugin found in marketplace.json with relative path source
- **WHEN** `fetch(spec, cache_dir)` is called with `spec.prompt_name` equal to `"code-simplifier"`
- **AND** `marketplace.json` contains an entry with `"name": "code-simplifier"` and `"source": "./plugins/code-simplifier"`
- **THEN** the fetcher resolves the plugin source path to `plugins/code-simplifier`

#### Scenario: Plugin not found in marketplace.json
- **WHEN** `fetch(spec, cache_dir)` is called with a prompt name that does not match any entry
- **THEN** a `SyncError` is raised with a message indicating the plugin was not found

#### Scenario: Plugin has external git URL source (skipped for MVP)
- **WHEN** `marketplace.json` contains an entry with `"source": {"source": "url", "url": "https://..."}`
- **AND** `fetch(spec, cache_dir)` is called for that plugin
- **THEN** a `SyncError` is raised indicating external sources are not yet supported

#### Scenario: marketplace.json fetch fails
- **WHEN** the HTTP request for `marketplace.json` fails (network error or non-200 status)
- **THEN** a `SyncError` is raised with a message describing the failure

### Requirement: ClaudeMarketplaceFetcher downloads ALL files in plugin directory
The fetcher SHALL download every file in the plugin directory tree — `.md`, `.json`, scripts, configs, and any other file type — to the cache directory.

#### Scenario: Plugin with mixed file types
- **WHEN** the plugin directory contains `agents/reviewer.md`, `.claude-plugin/plugin.json`, `hooks/hooks.json`, `scripts/check.sh`
- **THEN** all 4 files are downloaded to the cache directory preserving their relative paths
- **AND** the returned `Plugin.files` lists all 4 relative paths

#### Scenario: Plugin directory listing fails
- **WHEN** the GitHub Contents API returns a non-200 status for the plugin directory
- **THEN** a `SyncError` is raised

### Requirement: ClaudeMarketplaceFetcher handles skills repo structure
The fetcher SHALL support the skills repo structure where plugins declare a `skills` array in `marketplace.json` pointing to skill directories.

#### Scenario: Plugin with skills array
- **WHEN** `marketplace.json` contains an entry with `"source": "./"` and `"skills": ["./skills/xlsx", "./skills/docx"]`
- **THEN** the fetcher downloads all files from each listed skill directory
- **AND** the `Plugin.files` includes paths like `skills/xlsx/SKILL.md`, `skills/xlsx/scripts/processor.py`, `skills/docx/SKILL.md`

### Requirement: ClaudeMarketplaceFetcher retrieves commit SHA for cache key
The fetcher SHALL get the latest commit SHA from the GitHub API to use as the cache directory key.

#### Scenario: Commit SHA retrieved
- **WHEN** the fetcher queries the GitHub API for the default branch
- **THEN** the latest commit SHA is used as part of the cache path `{registry}/{plugin}/{sha}/`
- **AND** the returned `Plugin.commit_sha` matches

### Requirement: ClaudeMarketplaceFetcher parses GitHub repository URL
The fetcher SHALL extract `owner` and `repo` from the registry URL to construct API requests.

#### Scenario: Standard GitHub URL
- **WHEN** constructed with `registry_url="https://github.com/anthropics/claude-plugins-official"`
- **THEN** API requests target `api.github.com/repos/anthropics/claude-plugins-official/...`

#### Scenario: Invalid URL format
- **WHEN** constructed with a URL that does not match `https://github.com/{owner}/{repo}`
- **THEN** a `SyncError` is raised at construction time

### Requirement: ClaudeMarketplaceFetcher accepts injectable httpx.Client
The fetcher SHALL accept an optional `httpx.Client` parameter for testability.

#### Scenario: Custom client provided
- **WHEN** constructed with `client=mock_client`
- **THEN** all HTTP requests use the provided client

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
- **AND** skills directory maps to `skills-cursor/`
