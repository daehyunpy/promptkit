# Cursor Directory Structure Reference

> **Reference snapshot** — upstream `.cursor/` directory spec for promptkit builder design.
> This is NOT a promptkit doc. It tracks upstream platform constraints.

| Field | Value |
|-------|-------|
| Source | https://docs.cursor.com, community docs, https://cursor.directory |
| Captured | 2026-02-10 |
| cursor/cursor commit | `53a1e5adf5b0` (2026-01-30) |

**Note**: Cursor has no single published directory spec. This is assembled from official docs, community sources, and observed behavior.

---

## Directory Structure

```
.cursor/
├── rules/                     # Project rules (FLAT)
│   └── *.mdc                  #   .mdc format (markdown + YAML frontmatter)
├── skills/                    # Skills (ONE LEVEL nesting — Agent Skills standard)
│   └── <name>/
│       ├── SKILL.md           # Required entrypoint
│       ├── scripts/           # Optional support files
│       └── reference.md       # Optional references
└── skill-packs/               # Optional skill pack configs
    └── *.json                 #   Switch between skill configurations
```

Legacy: `.cursorrules` file at project root (deprecated, replaced by `.cursor/rules/*.mdc`).

---

## Nesting Constraints

| Component | Structure | Max Depth | Notes |
|-----------|-----------|-----------|-------|
| **Skills** | `skills/<name>/SKILL.md` | 1 level | Same Agent Skills standard as Claude Code |
| **Rules** | `rules/*.mdc` | Flat | No subdirectories |

---

## .mdc Rule Format

```yaml
---
description: Short description of the rule's purpose
globs: src/**/*.ts, lib/**/*.js
alwaysApply: false
---

Rule content in markdown...
```

### Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Shown in UI and used for filtering. Required for "agent requested" mode. |
| `globs` | string | Comma-separated file glob patterns. Required for "auto attached" mode. |
| `alwaysApply` | boolean | If `true`, always included in context (globs ignored). Default: `false`. |

### Four Rule Types (Activation Modes)

The combination of frontmatter values determines how the rule is activated:

| Type | `alwaysApply` | `globs` | `description` | Behavior |
|------|--------------|---------|--------------|----------|
| **Always** | `true` | — | — | Always in context |
| **Auto Attached** | `false` | set | — | Included when matching files are referenced |
| **Agent Requested** | `false` | — | set | AI decides based on description |
| **Manual** | `false` | — | — | Only via `@ruleName` mention |

### Behavior Notes

- `alwaysApply: true` with `globs:` → globs are ignored, rule always applies
- `globs:` only (no `alwaysApply`) → auto-attach mode, only when matching files are in context
- No fields set → manual mode, only included when explicitly `@`-mentioned
- Naming: kebab-case filenames, always `.mdc` extension

### Rule Precedence

Team Rules → Project Rules → User Rules. All applicable rules are merged; earlier sources take priority on conflict.

---

## SKILL.md Format

Same [Agent Skills](https://agentskills.io) open standard as Claude Code:

```yaml
---
name: skill-name
description: What this skill does and when to use it
---

Skill instructions in markdown...
```

Cursor skills support:
- `name` — Display name / slash command trigger
- `description` — Used for auto-invocation by agent

Cursor does NOT support these Claude Code-specific fields:
- `disable-model-invocation`
- `user-invocable`
- `allowed-tools`
- `model`
- `context` / `agent`
- `hooks`

### Skill Packs

Cursor supports "skill packs" — JSON configs in `.cursor/skill-packs/` that define which skills are active. Skills not in the active pack are moved to `.cursor/skills-optional/`.

---

## What Cursor DOESN'T Have (file-based)

| Feature | Claude Code | Cursor |
|---------|-------------|--------|
| Agents/subagents | `agents/*.md` | IDE-integrated (Background Agent), not file-based |
| Commands | `commands/*.md` | IDE command palette, not file-based |
| Hooks | `hooks/hooks.json` | No hook system |
| MCP servers | `.mcp.json` | Configured through IDE settings UI |
| LSP servers | `.lsp.json` | Built-in to the IDE |
| Memory | `agent-memory/` | No equivalent |

---

## promptkit Builder Implications

**Cursor builder** copies to `.cursor/`:
- `skills/<name>/` → `.cursor/skills/<name>/` (preserves structure, same standard)

**Everything else from upstream plugins is skipped** — Cursor has no file-based equivalent for agents, commands, hooks, MCP, or LSP.

**Rules**: Cursor uses `.mdc` rules instead of agents/commands. promptkit does NOT generate rules — that's a different concern (project conventions, not fetched prompts).
