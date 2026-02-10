## Context

Phases 1-7 are complete (init, lock, build, sync). The `YamlLoader` already validates config syntax (invalid YAML, missing version/prompts, invalid platform keys). The validate command adds higher-level semantic checks: registry references, prompt existence, and lock file freshness.

The existing `ValidationError` is already used by `YamlLoader`. The validate use case will collect multiple errors rather than failing on the first one.

## Goals / Non-Goals

**Goals:**
- Validate config is well-formed (delegates to `YamlLoader.load()`)
- Validate prompts reference defined registries
- Validate local prompts in lock file exist on disk
- Detect stale lock file (config changed since last lock)
- Report all issues at once (not fail-fast)
- Add `promptkit validate` CLI command

**Non-Goals:**
- No network validation (don't check if remote prompts exist)
- No content validation (don't verify prompt markdown format)
- No lock file integrity checks (don't verify hashes match cached content)
- No auto-fix capabilities

## Decisions

### 1. ValidateConfig as an application-layer use case

Create `app/validate.py` with a `ValidateConfig` class that returns a list of validation issues. This follows the existing pattern of `LockPrompts` and `BuildArtifacts`.

**Rationale:** Validation is a distinct operation from lock/build. It needs to collect multiple errors rather than fail on the first one, which is different from the fail-fast approach in other use cases.

**Alternative considered:** Adding validation methods to existing use cases. Rejected because validate needs to report all issues without side effects.

### 2. Return a result object, not raise exceptions

`ValidateConfig.execute()` returns a `ValidationResult` dataclass containing a list of issues (each with a severity level and message). The CLI handler decides how to display them and what exit code to use.

**Rationale:** Validation should report everything it finds, not stop at the first error. A result object gives the CLI flexibility in formatting.

**Alternative considered:** Raising `ValidationError` with all messages. Rejected because exceptions should represent failures, not reports with varying severity.

### 3. Three validation checks

1. **Config well-formed** — Delegate to `YamlLoader.load()`. If it raises `ValidationError`, capture the message.
2. **Registry references valid** — For each prompt spec, check that `spec.registry_name` exists in the config's registries list.
3. **Lock freshness** — If `promptkit.lock` exists, verify every config prompt appears in the lock and no lock entries are stale (source not in config).

**Rationale:** These are the checks that catch real user mistakes: typos in registry names, forgotten lock runs, and removed prompts that still appear in the lock file.

### 4. ValidationResult and ValidationIssue value objects

```python
@dataclass(frozen=True)
class ValidationIssue:
    level: str  # "error" or "warning"
    message: str

@dataclass(frozen=True)
class ValidationResult:
    issues: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not any(i.level == "error" for i in self.issues)
```

Errors cause exit code 1. Warnings are informational (e.g., stale lock).

## Risks / Trade-offs

- **[Risk] Lock freshness is heuristic** — We compare config prompt sources with lock entry sources, not content hashes. Mitigation: this catches the most common case (added/removed prompts in config) without needing to re-fetch.
- **[Risk] Validation result grows complex** — For MVP, keep it simple: just level + message. No structured error codes or fix suggestions.
