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

## What Codex DOESN'T Have (vs Claude Code)

| Feature | Claude Code | Codex |
|---------|-------------|-------|
| Agents/subagents | `agents/*.md` | No file-based equivalent |
| Commands | `commands/*.md` | No file-based equivalent |
| Hooks | `hooks/hooks.json` | `notify` in config.toml only |
| MCP servers | `.mcp.json` | Configured in `config.toml` |
| LSP servers | `.lsp.json` | No equivalent |
| Memory | `agent-memory/` | No equivalent |
| Rules | N/A | N/A (uses AGENTS.md) |

---

## promptkit Builder Implications

**Codex builder** copies to `.codex/`:
- `skills/<name>/` → `.codex/skills/<name>/` (preserves structure, same Agent Skills standard)

**Everything else from upstream plugins is skipped** — Codex has no file-based equivalent for agents, commands, hooks, MCP, or LSP. Instructions go in `AGENTS.md` (user-managed, not promptkit-generated).

**Also valid**: `.agents/skills/` is an alternative skills location. However, `.codex/skills/` is the project-level convention that matches the platform's own directory (like `.cursor/skills/` and `.claude/skills/`). Using `.codex/` as the output dir keeps promptkit consistent across all three platforms.
