## ADDED Requirements

### Requirement: ClaudeMarketplaceFetcher reads marketplace.json to resolve plugin paths
The `ClaudeMarketplaceFetcher` SHALL fetch `.claude-plugin/marketplace.json` from the registry repository and use it to resolve the plugin's source path within the repo.

#### Scenario: Plugin found in marketplace.json
- **WHEN** `fetch(spec)` is called with `spec.prompt_name` equal to `"code-simplifier"`
- **AND** `marketplace.json` contains an entry with `"name": "code-simplifier"` and `"source": "./plugins/code-simplifier"`
- **THEN** the fetcher resolves the plugin source path to `plugins/code-simplifier`

#### Scenario: Plugin not found in marketplace.json
- **WHEN** `fetch(spec)` is called with a prompt name that does not match any entry in `marketplace.json`
- **THEN** a `SyncError` is raised with a message indicating the plugin was not found in the registry

#### Scenario: marketplace.json fetch fails
- **WHEN** `fetch(spec)` is called and the HTTP request for `marketplace.json` fails (network error or non-200 status)
- **THEN** a `SyncError` is raised with a message describing the failure

### Requirement: ClaudeMarketplaceFetcher discovers .md files in plugin directories
The fetcher SHALL use the GitHub Contents API to list the plugin's source directory and recursively discover `.md` files in category subdirectories (`agents/`, `commands/`, `skills/`, etc.).

#### Scenario: Single-file plugin (one agent)
- **WHEN** the plugin directory contains `agents/code-simplifier.md` and no other category subdirs
- **THEN** `fetch()` returns a list with one `Prompt` whose content is the `.md` file content

#### Scenario: Multi-file plugin (agents + commands)
- **WHEN** the plugin directory contains `agents/code-architect.md`, `agents/code-explorer.md`, `agents/code-reviewer.md`, and `commands/feature-dev.md`
- **THEN** `fetch()` returns a list of 4 `Prompt` objects, one per `.md` file

#### Scenario: Non-.md files are ignored
- **WHEN** the plugin directory contains `README.md`, `.claude-plugin/plugin.json`, and `agents/my-agent.md`
- **THEN** only files inside category subdirectories are returned (not `README.md` at root level)
- **AND** non-`.md` files like `plugin.json` are ignored

#### Scenario: Plugin directory listing fails
- **WHEN** the GitHub Contents API returns a non-200 status for the plugin directory
- **THEN** a `SyncError` is raised

### Requirement: ClaudeMarketplaceFetcher handles skills repo structure
The fetcher SHALL support the skills repo structure where plugins declare a `skills` array in `marketplace.json` pointing to skill directories containing `SKILL.md`.

#### Scenario: Plugin with skills array
- **WHEN** `marketplace.json` contains an entry with `"skills": ["./skills/xlsx", "./skills/docx"]`
- **THEN** the fetcher fetches `SKILL.md` from each skill path
- **AND** returns a list of `Prompt` objects, one per skill

#### Scenario: Skill directory has no SKILL.md
- **WHEN** a skill path from the `skills` array has no `SKILL.md` file
- **THEN** a `SyncError` is raised indicating the missing skill file

### Requirement: ClaudeMarketplaceFetcher constructs correct source paths for prompts
Each `Prompt` returned by the fetcher SHALL have a source path formatted as `{registry_name}/{category}/{filename}` to enable correct category routing during build.

#### Scenario: Source path for plugin agent
- **WHEN** registry name is `claude-plugins-official` and the file is `agents/code-reviewer.md` inside plugin `feature-dev`
- **THEN** the prompt source is `claude-plugins-official/agents/code-reviewer`

#### Scenario: Source path for plugin command
- **WHEN** registry name is `claude-plugins-official` and the file is `commands/feature-dev.md` inside plugin `feature-dev`
- **THEN** the prompt source is `claude-plugins-official/commands/feature-dev`

#### Scenario: Source path for skill
- **WHEN** registry name is `anthropic-agent-skills` and the file is `skills/xlsx/SKILL.md`
- **THEN** the prompt source is `anthropic-agent-skills/skills/xlsx`

### Requirement: ClaudeMarketplaceFetcher parses GitHub repository URL
The fetcher SHALL extract `owner` and `repo` from the registry URL (`https://github.com/{owner}/{repo}`) to construct GitHub API requests.

#### Scenario: Standard GitHub URL
- **WHEN** constructed with `registry_url="https://github.com/anthropics/claude-plugins-official"`
- **THEN** API requests target `api.github.com/repos/anthropics/claude-plugins-official/contents/...`

#### Scenario: Invalid URL format
- **WHEN** constructed with a URL that does not match `https://github.com/{owner}/{repo}`
- **THEN** a `SyncError` is raised at construction time

### Requirement: ClaudeMarketplaceFetcher accepts injectable httpx.Client
The fetcher SHALL accept an optional `httpx.Client` parameter for testability. When not provided, it SHALL create its own client.

#### Scenario: Custom client provided
- **WHEN** constructed with `client=mock_client`
- **THEN** all HTTP requests use the provided client

#### Scenario: No client provided
- **WHEN** constructed without a `client` parameter
- **THEN** the fetcher creates and uses a default `httpx.Client`
