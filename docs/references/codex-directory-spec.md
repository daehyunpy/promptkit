# Codex CLI Directory Structure Reference

> **Reference snapshot** — upstream `.codex/` directory spec for promptkit builder design.
> This is NOT a promptkit doc. It tracks upstream platform constraints.

| Field | Value |
|-------|-------|
| Source | https://developers.openai.com/codex/skills/, https://developers.openai.com/codex/config-basic/, https://developers.openai.com/codex/guides/agents-md/ |
| Captured | 2026-02-18 |
| openai/codex version | codex-cli ~0.91 (2026-01) |

**Note**: Assembled from official OpenAI developer docs, GitHub repo, and community sources.

---

## Directory Structure

Codex uses two project-level directories plus root-level instruction files:

```
<project-root>/
├── AGENTS.md                      # Project instructions (root-level)
├── AGENTS.override.md             # Temporary override (root-level)
├── .codex/
│   ├── config.toml                # Project-scoped configuration
│   └── skills/                    # Project skills (ONE LEVEL nesting)
│       └── <name>/
│           ├── SKILL.md           # Required entrypoint
│           ├── scripts/           # Optional support files
│           ├── references/        # Optional documentation
│           ├── assets/            # Optional templates/data
│           ├── examples/          # Optional sample inputs/outputs
│           └── agents/
│               └── openai.yaml    # Optional skill metadata for Codex app
├── .agents/
│   └── skills/                    # Open Agent Skills standard location
│       └── <name>/
│           └── SKILL.md           # Same format as .codex/skills/
└── <subdir>/
    └── AGENTS.md                  # Directory-specific instructions (walked)
```

User-level equivalents live at `~/.codex/` with the same structure plus `~/.codex/skills/.system/` for built-in skills.

---

## Skill Discovery

Codex reads skills from multiple locations in this priority order:

| Location | Scope | Description |
|----------|-------|-------------|
| `~/.codex/skills/.system/` | System | Built-in skills (plan, skill-creator, skill-installer) |
| `~/.codex/skills/` | User | Personal skills across all projects |
| `.codex/skills/` (in repo) | Project | Shared team skills checked into version control |
| `.agents/skills/` (in repo) | Project (standard) | Open Agent Skills standard — scanned per-directory up to repo root |

For `.agents/skills/`, Codex scans every directory from CWD up to the repository root. If two skills share the same name, Codex does NOT merge them; both appear in skill selectors.

Skills use **progressive disclosure**: Codex loads only metadata (name, description) at startup and reads the full `SKILL.md` body only when the skill is invoked.

---

## SKILL.md Format

```yaml
---
name: skill-name                    # kebab-case (required)
description: What this skill does   # required — used for auto-invocation
---

Skill instructions in markdown...
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name / invocation trigger |
| `description` | string | Yes | Used for implicit invocation matching |

Codex's SKILL.md frontmatter is minimal compared to Claude Code. Codex does NOT support these Claude Code-specific fields:
- `disable-model-invocation`
- `user-invocable`
- `allowed-tools`
- `model`
- `context` / `agent`
- `hooks`
- `argument-hint`

### Optional Metadata File

Add `agents/openai.yaml` inside a skill directory to configure UI metadata in the Codex app, set invocation policy (`allow_implicit_invocation`), and declare tool dependencies.

### Skill Invocation

- **Explicit**: Type `$skill-name` or use `/skills` to browse
- **Implicit**: Codex auto-selects when task matches skill description (controlled by `allow_implicit_invocation`)

### Disabling Skills

Use `[[skills.config]]` entries in `config.toml`:
```toml
[[skills.config]]
path = ".codex/skills/my-skill/SKILL.md"
enabled = false
```

---

## Slash Commands

Codex has built-in slash commands (CLI features, not file-based artifacts):

| Command | Description |
|---------|-------------|
| `/plan` | Switch conversation to plan mode |
| `/review` | Launch code review on a selected diff |
| `/model` | Switch models or adjust reasoning levels |
| `/personality` | Change communication style (friendly, pragmatic, none) |
| `/skill` | Browse, enable, or disable individual skills |
| `/permissions` | Manage approval policy settings |
| `/m_update`, `/m_drop` | Memory management (TUI) |
| `/quit` / `/exit` | Exit Codex |
| `/logout` | Clear local credentials |

User-defined slash commands were the deprecated custom prompts (see below). Skills use `$skill-name` syntax for explicit invocation, not `/` prefix.

---

## Instruction Discovery (AGENTS.md)

Codex builds an instruction chain at startup:

1. **Global scope**: `~/.codex/AGENTS.override.md` → `~/.codex/AGENTS.md` (first non-empty wins)
2. **Project scope**: Walks from project root to CWD, at each level checks:
   - `AGENTS.override.md`
   - `AGENTS.md`
   - Fallback names from `project_doc_fallback_filenames` config

Files are concatenated root-down, capped at `project_doc_max_bytes` (32 KiB default).

---

## Configuration (config.toml)

Project-level config at `.codex/config.toml`. Codex walks from project root to CWD loading every `.codex/config.toml` it finds (closest wins).

Key config areas:
- Model and provider settings
- Approval policies and sandbox settings
- MCP server definitions
- Profiles (`[profiles.<name>]`)
- Features (`[features]` table)
- Skills config (`[[skills.config]]`)
- Environment variable forwarding
- Log file locations

**Trust model**: Project-scoped `.codex/` config is only loaded for trusted projects. Untrusted projects fall back to user/system defaults.

---

## Nesting Constraints

| Component | Structure | Max Depth | Notes |
|-----------|-----------|-----------|-------|
| **Skills** | `skills/<name>/SKILL.md` | 1 level | Subdirs OK inside skill dir (scripts/, references/, etc.) |
| **Instructions** | `AGENTS.md` at each directory level | N/A | Walked from root to CWD |
| **Config** | `.codex/config.toml` | N/A | Walked from root to CWD |

---

## Feature Comparison (vs Claude Code)

| Feature | Claude Code | Codex | Notes |
|---------|-------------|-------|-------|
| Skills | `.claude/skills/<name>/SKILL.md` | `.codex/skills/<name>/SKILL.md` | Same Agent Skills standard, both file-based |
| Agents/subagents | `.claude/agents/*.md` | Multi-agent roles in `config.toml` | Codex uses TOML config, not separate `.md` files |
| Commands | `.claude/commands/*.md` | Custom prompts in `~/.codex/prompts/` **(deprecated)** | Deprecated — replaced by skills |
| Hooks | `.claude/hooks/hooks.json` | `notify` array in `config.toml` | Codex only has a post-turn notify hook |
| MCP servers | `.claude/.mcp.json` | `[mcp_servers.*]` in `config.toml` | Both STDIO and HTTP; configured per-project in `.codex/config.toml` |
| LSP servers | `.claude/.lsp.json` | No equivalent | — |
| Memory | `.claude/agent-memory/` | No equivalent | — |
| Rules | N/A | N/A | Both use instruction files (CLAUDE.md / AGENTS.md) |
| Project instructions | `CLAUDE.md` | `AGENTS.md` (+ `AGENTS.override.md`) | Both at project root, Codex walks subdirs |
| Project config | `.claude/settings.json` | `.codex/config.toml` | Codex uses TOML, walked from root to CWD |

---

## MCP Server Configuration

MCP servers are configured in `config.toml` (not a separate JSON file like Claude Code):

```toml
[mcp_servers.my-server]
command = "npx"
args = ["-y", "@my-org/my-mcp-server"]
env = { API_KEY = "..." }
enabled = true
startup_timeout_sec = 30
tool_timeout_sec = 60
```

Key fields: `command`, `args`, `env`, `env_vars`, `cwd`, `bearer_token_env_var`, `http_headers`, `env_http_headers`, `startup_timeout_sec`, `tool_timeout_sec`, `enabled`, `required`, `enabled_tools`, `disabled_tools`.

Project-scoped MCP servers go in `.codex/config.toml` (trusted projects only).

---

## Custom Prompts (Deprecated)

Custom prompts lived in `~/.codex/prompts/<name>.md` — flat Markdown files that became slash commands (`/prompts:<name>`). They supported `$1`–`$9` positional args and `$ARGUMENTS`.

**Deprecated** — replaced by skills, which support both explicit and implicit invocation and can be shared via the repository.

---

## promptkit Builder Implications

**Codex builder** copies to `.codex/`:
- `skills/<name>/` → `.codex/skills/<name>/` (preserves structure, same Agent Skills standard)

**Agents, commands, hooks, MCP** — Codex has these features but they're all configured in `config.toml`, not as separate file trees. promptkit cannot merge TOML config fragments from plugins into a user's config, so these categories are skipped. If Codex later adds file-based equivalents (like `.codex/agents/*.md`), the builder can be updated.

**Also valid**: `.agents/skills/` is an alternative skills location. However, `.codex/skills/` is the project-level convention that matches the platform's own directory (like `.cursor/skills/` and `.claude/skills/`). Using `.codex/` as the output dir keeps promptkit consistent across all three platforms.
