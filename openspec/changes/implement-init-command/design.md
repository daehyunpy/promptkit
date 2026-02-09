## Context

The Python project foundation is in place with DDD structure (domain, app, infra layers). We're implementing the first user-facing CLI command: `promptkit init`. This command must scaffold a new promptkit project in the current directory.

**Current state:**
- CLI entry point declared in pyproject.toml: `promptkit = "promptkit.cli:app"`
- No cli.py module exists yet
- typer is installed as a dependency
- DDD layer structure is ready for domain models and use cases

**Constraints:**
- Follow DDD, TDD, and Clean Code principles (per AGENTS.md)
- Keep domain logic in domain layer (no file I/O)
- Keep infrastructure logic in infra layer (file operations)
- Application layer orchestrates, doesn't contain logic

## Goals / Non-Goals

**Goals:**
- Implement `promptkit init` as the first CLI command
- Scaffold complete promptkit project structure
- Generate valid `promptkit.yaml` with example configuration
- Support running in existing directories (non-destructive)
- Provide clear success/error messages
- Follow DDD layering strictly

**Non-Goals:**
- Interactive prompts for configuration (use sensible defaults)
- Overwriting existing files (fail safely if files exist)
- Validating git repository (user can init outside git)
- Installing dependencies or running setup scripts
- Creating sample prompts in `.agents/` (empty directory is fine)

## Decisions

### 1. CLI Framework: Typer with Single Command

**Decision:** Use typer's app decorator pattern with `init` as a command function.

**Rationale:**
- typer is already installed and configured in pyproject.toml
- Clean, type-safe CLI interface with minimal boilerplate
- Automatic help text generation from docstrings
- Consistent with modern Python CLI conventions

**Structure:**
```python
# source/promptkit/cli.py
import typer

app = typer.Typer()

@app.command()
def init():
    """Initialize a new promptkit project."""
    # Implementation calls InitProject use case
```

**Alternatives considered:**
- Click: More verbose, typer is built on click anyway
- Argparse: Too low-level, more boilerplate

### 2. Application Layer: InitProject Use Case

**Decision:** Create `InitProject` class in `app/init.py` that orchestrates initialization.

**Rationale:**
- Separates orchestration logic from CLI layer
- Testable independently of typer
- Follows application layer pattern: coordinate domain and infrastructure
- No domain logic here - just calls file system and domain objects

**Structure:**
```python
# source/promptkit/app/init.py
class InitProject:
    def __init__(self, file_system: FileSystemProtocol):
        self.file_system = file_system

    def execute(self, target_dir: Path) -> None:
        # Create directories
        # Generate config
        # Write files
```

**Alternatives considered:**
- Function instead of class: Rejected because dependency injection (FileSystemProtocol) is cleaner with a class
- Put logic directly in CLI: Violates DDD layering, makes testing harder

### 3. Domain Layer: ProjectConfig Value Object

**Decision:** Create `ProjectConfig` value object to represent promptkit.yaml structure.

**Rationale:**
- Domain concept: the configuration of a promptkit project
- Immutable value object (no identity)
- Can validate structure and provide defaults
- Can serialize to YAML (via a method or property)

**Structure:**
```python
# source/promptkit/domain/project_config.py
@dataclass(frozen=True)
class ProjectConfig:
    version: int
    prompts: list[PromptEntry]
    platforms: dict[str, PlatformConfig]

    @classmethod
    def default(cls) -> "ProjectConfig":
        """Return default configuration."""
        ...

    def to_yaml_string(self) -> str:
        """Serialize to YAML string."""
        ...
```

**Alternatives considered:**
- Dict directly: No type safety, no validation, no behavior
- Pydantic model: Over-engineering for v1, adds runtime validation we don't need yet

### 4. Infrastructure Layer: File System Operations

**Decision:** Create `FileSystemProtocol` and `LocalFileSystem` implementation in `infra/file_system.py`.

**Rationale:**
- Infrastructure concern: file I/O is external dependency
- Protocol allows test doubles (in-memory file system for tests)
- Clean boundary: domain/app layers depend on protocol, not implementation
- All file operations in one place

**Protocol:**
```python
# source/promptkit/infra/file_system.py
class FileSystemProtocol(Protocol):
    def create_directory(self, path: Path) -> None: ...
    def write_file(self, path: Path, content: str) -> None: ...
    def file_exists(self, path: Path) -> bool: ...
    def append_to_file(self, path: Path, content: str) -> None: ...

class LocalFileSystem:
    """Implementation for local file system."""
    def create_directory(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
    ...
```

**Alternatives considered:**
- Use pathlib directly in app layer: Violates clean architecture, hard to test
- Use existing libraries (fsspec): Over-engineering, adds dependency

### 5. Directory Structure to Create

**Decision:** Create these directories in order:
1. `.promptkit/cache/` (for synced prompts)
2. `.agents/` (for canonical/custom prompts)
3. `.cursor/` (for Cursor artifacts)
4. `.claude/` (for Claude Code artifacts)

**Rationale:**
- Matches structure defined in technical_design.md
- All required directories from MVP
- Empty directories are fine (populated by later commands)

**Alternatives considered:**
- Only create `.promptkit/cache/`: Users would have to create others manually
- Create subdirectories (e.g., `.cursor/agents/`): Premature, let build command handle it

### 6. promptkit.yaml Template Content

**Decision:** Generate minimal but functional config with one example prompt entry.

**Example:**
```yaml
version: 1

prompts:
  # Example prompt entry - uncomment and edit
  # - name: code-reviewer
  #   source: anthropic/code-reviewer
  #   platforms:
  #     - cursor
  #     - claude-code

platforms:
  cursor:
    output_dir: .cursor
  claude-code:
    output_dir: .claude
```

**Rationale:**
- Shows the expected structure
- Commented example teaches users the format
- Can be committed as-is (valid empty config)
- Platform settings show default output directories

**Alternatives considered:**
- Empty file: Users don't know what structure to use
- Fully populated: Might not match user's needs
- Interactive prompts: Out of scope for v1

### 7. Error Handling: Fail Fast on Existing Files

**Decision:** Check if `promptkit.yaml` exists before creating. If it does, exit with error.

**Rationale:**
- Non-destructive: don't overwrite user's config
- Clear error message guides user
- User can re-run init in different directory if needed

**Behavior:**
- Check: `promptkit.yaml` exists?
- If yes: Exit with error: "promptkit.yaml already exists. Remove it or run in a different directory."
- If no: Proceed with initialization

**Alternatives considered:**
- Force flag to overwrite: Adds complexity, can be added later if needed
- Interactive confirm: Out of scope for v1
- Merge/update existing: Too complex, could corrupt config

### 8. .gitignore Integration

**Decision:** If `.gitignore` exists, append promptkit entries. If not, create it.

**Entries to add:**
```
# promptkit
.promptkit/cache/
```

**Rationale:**
- `.promptkit/cache/` contains fetched prompts (reproducible via lock file)
- Other directories (`.agents/`, `.cursor/`, `.claude/`) user decides (optional)
- Non-intrusive: only add if `.gitignore` exists or create minimal one

**Alternatives considered:**
- Don't touch .gitignore: Users might commit cache by accident
- Always add all directories: Too opinionated, user should choose

### 9. Success Message with Next Steps

**Decision:** After successful init, print helpful message:

```
✓ Initialized promptkit project

Next steps:
  1. Edit promptkit.yaml to add prompts
  2. Run: promptkit sync
  3. Run: promptkit build

Created:
  - promptkit.yaml
  - promptkit.lock
  - .promptkit/cache/
  - .agents/
  - .cursor/
  - .claude/
```

**Rationale:**
- Guides user on what to do next
- Confirms what was created
- Establishes the workflow: init → sync → build

**Alternatives considered:**
- Minimal message: Less helpful for new users
- Verbose explanation: Too much, users can read docs

## Risks / Trade-offs

**[Risk: Creating files in existing project directory]**
- Mitigation: Check for `promptkit.yaml` first. Fail if exists. User can remove it if they want to re-init.

**[Risk: .gitignore conflicts]**
- Mitigation: Append to end of file with clear comment header. If user has custom .gitignore structure, they can manually edit.

**[Trade-off: Commented example vs empty config]**
- Including commented example teaches format but adds noise
- Benefit: Users learn structure immediately
- Cost: 5 extra lines in generated file

**[Trade-off: No interactive mode]**
- Simpler implementation, predictable behavior
- Benefit: Scriptable, deterministic
- Cost: Less user-friendly for beginners (can add --interactive later)

**[Risk: User runs init in wrong directory]**
- Mitigation: Clear error messages. Success message shows what was created so user can verify location.

## Migration Plan

**Deployment:**
1. Merge PR with init command implementation
2. Users can now run `promptkit init` after installing via `uv sync`
3. No migration needed (new feature, no existing data)

**Rollback:**
- Not applicable (new feature, no existing behavior to preserve)
- If broken, revert commit

**Validation:**
- CI: Run `promptkit init` in temp directory, verify files created
- CI: Run `promptkit init` twice in same directory, verify second fails appropriately
- Manual: Test in real project directory

## Open Questions

None. All design decisions are based on constraints from AGENTS.md, technical design, and MVP requirements from PRD.
