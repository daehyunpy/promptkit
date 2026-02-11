## MODIFIED Requirements

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

### Requirement: ClaudeMarketplaceFetcher retrieves commit SHA for cache key
The fetcher SHALL get the commit SHA from the local git clone using `GitRegistryClone.get_commit_sha()` instead of the GitHub Commits API.

#### Scenario: Commit SHA retrieved from local clone
- **WHEN** the fetcher queries the local clone for the HEAD commit
- **THEN** the commit SHA from `git rev-parse HEAD` is used as part of the cache path `{registry}/{plugin}/{sha}/`
- **AND** the returned `Plugin.commit_sha` matches

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

### Requirement: ClaudeMarketplaceFetcher parses GitHub repository URL
The fetcher SHALL extract `owner` and `repo` from the registry URL to construct the git clone URL.

#### Scenario: Standard GitHub URL
- **WHEN** constructed with `registry_url="https://github.com/anthropics/claude-plugins-official"`
- **THEN** the clone URL is `https://github.com/anthropics/claude-plugins-official.git`

#### Scenario: Invalid URL format
- **WHEN** constructed with a URL that does not match `https://github.com/{owner}/{repo}`
- **THEN** a `SyncError` is raised at construction time

## REMOVED Requirements

### Requirement: ClaudeMarketplaceFetcher accepts injectable httpx.Client
**Reason**: HTTP client injection is no longer needed because the fetcher reads from the local git clone filesystem instead of making GitHub API calls.
**Migration**: Use `clone` parameter (GitRegistryClone) instead of `client` parameter (httpx.Client).
