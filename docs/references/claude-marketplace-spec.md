# Claude Code Plugin Marketplace Spec

> **Reference snapshot** — upstream documentation captured for promptkit development.
> This is NOT a promptkit doc. It tracks the upstream spec so we can detect breaking changes.

| Field | Value |
|-------|-------|
| Source | https://code.claude.com/docs/en/plugin-marketplaces |
| Captured | 2026-02-10 |
| claude-plugins-official commit | `2cd88e7947b7` (2026-02-06) |
| anthropic/skills commit | `1ed29a03dc85` (2026-02-06) |

---

## marketplace.json Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Marketplace identifier (kebab-case). Users see this: `/plugin install tool@name`. |
| `owner` | object | `{name: string, email?: string}` |
| `plugins` | array | List of plugin entries |

### Optional Metadata

| Field | Type | Description |
|-------|------|-------------|
| `metadata.description` | string | Brief marketplace description |
| `metadata.version` | string | Marketplace version |
| `metadata.pluginRoot` | string | Base dir prepended to relative source paths |

### Reserved Marketplace Names

`claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`,
`anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `life-sciences`.

---

## Plugin Entry Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier (kebab-case) |
| `source` | string \| object | Where to fetch the plugin (see Source Types below) |

### Optional Fields

**Standard metadata:**

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief plugin description |
| `version` | string | Semantic version |
| `author` | object | `{name: string, email?: string}` |
| `homepage` | string | Documentation URL |
| `repository` | string | Source code URL |
| `license` | string | SPDX identifier |
| `keywords` | array | Discovery tags |
| `category` | string | Organization category |
| `tags` | array | Searchability tags |
| `strict` | boolean | Default `true`. When false, marketplace entry defines plugin entirely. |

**Component configuration:**

| Field | Type | Description |
|-------|------|-------------|
| `commands` | string \| array | Paths to command files/directories |
| `agents` | string \| array | Paths to agent files |
| `skills` | string \| array | Paths to skill directories |
| `hooks` | string \| object | Hook configuration or path |
| `mcpServers` | string \| object | MCP server config or path |
| `lspServers` | string \| object | LSP server config or path |

---

## Source Types

### Relative Path (local within repo)

```json
{"name": "my-plugin", "source": "./plugins/my-plugin"}
```

Only works when marketplace is added via git clone (not URL-based).

### GitHub Repository

```json
{
  "name": "github-plugin",
  "source": {
    "source": "github",
    "repo": "owner/repo",
    "ref": "v2.0.0",
    "sha": "a1b2c3d4..."
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repo` | string | Yes | `owner/repo` format |
| `ref` | string | No | Branch or tag |
| `sha` | string | No | Full 40-char commit SHA |

### Git URL

```json
{
  "name": "git-plugin",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git",
    "ref": "main",
    "sha": "a1b2c3d4..."
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | Full git URL (must end `.git`) |
| `ref` | string | No | Branch or tag |
| `sha` | string | No | Full 40-char commit SHA |

---

## Plugin Directory Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest (optional)
├── commands/                  # Slash command markdown files
│   └── *.md
├── agents/                    # Subagent markdown files
│   └── *.md
├── skills/                    # Skills (dir/SKILL.md pattern)
│   └── <skill-name>/
│       ├── SKILL.md
│       └── scripts/           # Optional support files
├── hooks/
│   └── hooks.json
├── .mcp.json                  # MCP server definitions
├── .lsp.json                  # LSP server definitions
└── scripts/                   # Hook/utility scripts
```

Components must be at plugin root, NOT inside `.claude-plugin/`.

---

## plugin.json Manifest Schema

Only `name` is required. Rest is optional metadata + component paths.

```json
{
  "name": "plugin-name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": {"name": "...", "email": "..."},
  "homepage": "...",
  "repository": "...",
  "license": "MIT",
  "keywords": ["..."],
  "commands": ["./custom/commands/"],
  "agents": "./custom/agents/",
  "skills": "./custom/skills/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "lspServers": "./.lsp.json"
}
```

Custom paths SUPPLEMENT default directories — they don't replace them.

---

## Skills Format

Skills are directories containing `SKILL.md`:

```markdown
---
description: Review code for bugs, security, and performance
disable-model-invocation: true
---

Review the code I've selected or the recent changes for:
- Potential bugs or edge cases
- Security concerns
```

Frontmatter fields: `description` (string), `disable-model-invocation` (boolean).

---

## Agents Format

Agent markdown files with frontmatter:

```markdown
---
name: agent-name
description: What this agent specializes in
---

Detailed system prompt for the agent.
```

---

## Live Marketplace Snapshots

### claude-plugins-official (50+ plugins)

Commit: `2cd88e7947b7` (2026-02-06)

Key internal plugins (relative source, have agents/commands/skills):
- `feature-dev` — agents + commands for feature development
- `pr-review-toolkit` — PR review agents
- `code-simplifier` — code simplification agent
- `code-review` — automated code review
- `commit-commands` — git commit workflow commands
- `agent-sdk-dev` — Agent SDK development kit
- `plugin-dev` — plugin development toolkit
- `claude-code-setup` — codebase analysis for automations
- `claude-md-management` — CLAUDE.md maintenance tools
- `security-guidance` — security reminder hooks
- `frontend-design` — frontend UI generation
- `playground` — interactive HTML playground
- `ralph-loop` — iterative development loops
- `hookify` — custom hook creation
- `explanatory-output-style` — educational output
- `learning-output-style` — interactive learning

LSP-only plugins (no markdown prompt content):
- `typescript-lsp`, `pyright-lsp`, `gopls-lsp`, `rust-analyzer-lsp`,
  `clangd-lsp`, `php-lsp`, `swift-lsp`, `kotlin-lsp`, `csharp-lsp`,
  `jdtls-lsp`, `lua-lsp`

External plugins (git URL sources — different repos):
- `atlassian`, `figma`, `vercel`, `sentry`, `Notion`, `pinecone`,
  `huggingface-skills`, `firecrawl`, `coderabbit`, `posthog`,
  `sonatype-guide`, `circleback`, `superpowers`

External plugins (relative path, `./external_plugins/`):
- `greptile`, `serena`, `playwright`, `github`, `supabase`,
  `laravel-boost`, `asana`, `linear`, `gitlab`, `slack`, `stripe`,
  `firebase`, `context7`

### anthropic/skills (2 plugins, 16 skills)

Commit: `1ed29a03dc85` (2026-02-06)

```json
{
  "name": "anthropic-agent-skills",
  "owner": {"name": "Keith Lazuka", "email": "klazuka@anthropic.com"},
  "metadata": {"description": "Anthropic example skills", "version": "1.0.0"},
  "plugins": [
    {
      "name": "document-skills",
      "description": "Document processing: Excel, Word, PowerPoint, PDF",
      "source": "./",
      "strict": false,
      "skills": [
        "./skills/xlsx", "./skills/docx",
        "./skills/pptx", "./skills/pdf"
      ]
    },
    {
      "name": "example-skills",
      "description": "Example skills demonstrating various capabilities",
      "source": "./",
      "strict": false,
      "skills": [
        "./skills/algorithmic-art", "./skills/brand-guidelines",
        "./skills/canvas-design", "./skills/doc-coauthoring",
        "./skills/frontend-design", "./skills/internal-comms",
        "./skills/mcp-builder", "./skills/skill-creator",
        "./skills/slack-gif-creator", "./skills/theme-factory",
        "./skills/web-artifacts-builder", "./skills/webapp-testing"
      ]
    }
  ]
}
```

Note: Both plugins use `"source": "./"` (repo root) with `"strict": false`.
Skills are listed explicitly via the `skills` array, each pointing to a
directory containing `SKILL.md`.

---

## Implications for promptkit

1. **Plugin types vary widely** — LSP, MCP, hooks-only plugins have no markdown
   prompt content. The fetcher must handle plugins that have no agents/commands/skills.

2. **Source can be string OR object** — relative paths are strings, external
   sources are objects with `source`, `repo`/`url`, `ref`, `sha` fields.

3. **Skills repo uses `skills` array** — explicit list of skill dirs, not
   directory discovery. Each dir has `SKILL.md`.

4. **Plugins repo uses directory-based discovery** — plugin dir contains
   `agents/`, `commands/`, `skills/` subdirectories with `.md` files.

5. **`strict: false` + `source: "./"` pattern** — skills repo puts source at
   repo root and lists components explicitly in the marketplace entry.

6. **External plugins may reference other repos** — git URL sources point to
   entirely different repositories (e.g., figma, vercel, sentry).

7. **`metadata.pluginRoot`** — can change base directory for relative paths,
   meaning `"source": "formatter"` resolves to `"./plugins/formatter"` if
   `pluginRoot` is `"./plugins"`.
