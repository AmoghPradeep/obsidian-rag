## ADDED Requirements

### Requirement: Inference runtime is API-only
The system SHALL execute transcription, embedding, and text-generation workflows only through configured API services. The runtime MUST NOT load, eject, or manage local inference models as part of supported worker or MCP execution.

#### Scenario: Worker starts with API-backed runtime
- **WHEN** the background worker initializes model-related services
- **THEN** it uses configured API endpoints and remote model identifiers without creating local model runtime state

#### Scenario: MCP tools request generation
- **WHEN** an MCP tool invokes a generation or note-update flow
- **THEN** the request is sent through the supported API client path without any local fallback branch

### Requirement: Configuration and dependencies exclude local inference support
The repository SHALL expose only configuration and packaged dependencies that are required for the API-only deployment model. Local-model flags, local-runtime-only model settings, and local inference libraries MUST NOT remain in supported config surfaces or default installation metadata.

#### Scenario: Operator installs the project
- **WHEN** package metadata or `requirements.txt` is used to install the application
- **THEN** local inference libraries such as `transformers` and `torch` are not required by the supported install path

#### Scenario: Operator reviews configuration
- **WHEN** a user reads configuration defaults, environment variable mappings, or runbook examples
- **THEN** they see API endpoint and remote model settings only, without local transcription or local model fallback options
