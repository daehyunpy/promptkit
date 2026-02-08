# promptkit

A package manager for AI prompts. Sync high-quality prompts from sources like the Claude plugin marketplace, store them in version control, and generate platform-specific artifacts for tools like Cursor and Claude Code.

## Why promptkit?

- **Portable** - Same prompts work across multiple AI coding tools
- **Version-controlled** - Track changes and maintain reproducibility with lock files
- **No manual maintenance** - Eliminates copy/paste, format conversions, and cross-project drift
- **No tool lock-in** - Switch between AI coding tools without losing your prompt library

## Status

🚧 **Pre-implementation** - Currently in planning phase. See `docs/product_requirements.md` for details.

## Quick Start (Coming Soon)

```bash
# Initialize a new project
promptkit init

# Sync prompts from upstream
promptkit sync anthropic/code-reviewer

# Build platform-specific artifacts
promptkit build

# Validate configuration
promptkit validate
```

## Documentation

- [Product Requirements](docs/product_requirements.md) - What and why
- [Agent Instructions](AGENTS.md) - For AI agents working on this codebase

## Project Structure

```
promptkit.yaml          # Declarative config
promptkit.lock          # Version lock file
.promptkit/cache/       # Cached upstream prompts
.agents/                # Canonical/custom prompts
.cursor/                # Generated Cursor artifacts
.claude/                # Generated Claude Code artifacts
```

## License

TBD
