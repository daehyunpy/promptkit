## ADDED Requirements

### Requirement: Validate config is well-formed
The `ValidateConfig` use case SHALL verify that `promptkit.yaml` is valid YAML with all required fields by delegating to `YamlLoader.load()`.

#### Scenario: Valid config
- **WHEN** validate is run with a well-formed `promptkit.yaml`
- **THEN** no config-related errors are reported

#### Scenario: Invalid YAML syntax
- **WHEN** validate is run with malformed YAML
- **THEN** a validation error is reported with the YAML parse error message

#### Scenario: Missing required fields
- **WHEN** validate is run with a config missing `version` or `prompts`
- **THEN** a validation error is reported identifying the missing field

### Requirement: Validate prompt registry references
The `ValidateConfig` use case SHALL verify that each prompt's registry name matches a defined registry in the config.

#### Scenario: Valid registry reference
- **WHEN** a prompt references `my-registry/code-review` and `my-registry` is defined in registries
- **THEN** no registry-related errors are reported

#### Scenario: Unknown registry reference
- **WHEN** a prompt references `unknown-registry/code-review` but `unknown-registry` is not defined in registries
- **THEN** a validation error is reported: registry 'unknown-registry' is not defined

#### Scenario: No prompts configured
- **WHEN** the config has an empty prompts list
- **THEN** no registry-related errors are reported

### Requirement: Validate lock freshness
The `ValidateConfig` use case SHALL check that the lock file is consistent with the current config when a lock file exists.

#### Scenario: Lock matches config
- **WHEN** every config prompt has a corresponding lock entry and no stale entries exist
- **THEN** no lock-related warnings are reported

#### Scenario: Config prompt missing from lock
- **WHEN** a prompt is in the config but not in the lock file
- **THEN** a warning is reported: prompt 'X' is not locked, run 'promptkit lock'

#### Scenario: Stale lock entry
- **WHEN** a lock entry exists for a prompt that is no longer in the config
- **THEN** a warning is reported: lock entry 'X' is stale, run 'promptkit lock'

#### Scenario: No lock file exists
- **WHEN** no `promptkit.lock` file exists
- **THEN** a warning is reported: no lock file found, run 'promptkit lock'

### Requirement: Validation result collects all issues
The `ValidateConfig` use case SHALL collect all validation issues (errors and warnings) and return them as a `ValidationResult`, not fail on the first issue.

#### Scenario: Multiple issues reported
- **WHEN** the config has both an unknown registry and a stale lock entry
- **THEN** the result contains both issues

#### Scenario: Result is valid when no errors
- **WHEN** validation finds only warnings (no errors)
- **THEN** `result.is_valid` returns True

#### Scenario: Result is invalid when errors exist
- **WHEN** validation finds at least one error
- **THEN** `result.is_valid` returns False
