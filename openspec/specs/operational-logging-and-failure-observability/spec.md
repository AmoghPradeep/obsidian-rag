# operational-logging-and-failure-observability Specification

## Purpose
TBD - created by archiving change improve-operational-logging. Update Purpose after archive.
## Requirements
### Requirement: Critical execution paths emit contextual operational logs
The system SHALL emit operational logs for major execution stages and decision points across watcher scans, job execution, markdown generation, indexing, and MCP tool flows. These logs MUST include enough context to identify the operation being performed and the affected resource without requiring prompt or document content to be logged.

#### Scenario: Background ingestion processes a job
- **WHEN** the worker discovers, prepares, runs, retries, or finishes an ingestion job
- **THEN** the logs identify the job type, source path, and relevant stage or attempt number

#### Scenario: MCP tool flow runs
- **WHEN** an MCP tool starts, resolves a target, or completes an update or query path
- **THEN** the logs identify the tool action and outcome with contextual identifiers such as note reference, resolved path, or result counts

### Requirement: Exception catches emit error-level logs with actionable context
Every caught exception in supported runtime flows MUST emit an error-level log or `exception()` log that includes the operation name and the most relevant identifiers for the failed action.

#### Scenario: Pipeline stage raises an exception
- **WHEN** a background pipeline catches an exception while transcribing, rendering, writing markdown, or indexing
- **THEN** an error or exception log records the failing stage and the associated source or output path

#### Scenario: API or tool failure is caught
- **WHEN** an API client or MCP flow catches a generation, transcription, or tool-resolution failure
- **THEN** an error or exception log records the failing operation and contextual identifiers without logging full sensitive payloads

### Requirement: Log levels are used consistently by severity
The system SHALL use log levels consistently so routine lifecycle and state-transition events appear at `INFO`, low-level diagnostics appear at `DEBUG`, recoverable anomalies appear at `WARNING`, and caught failures appear at `ERROR` or `exception()`.

#### Scenario: Recoverable issue occurs
- **WHEN** the system defers an unstable folder, skips a duplicate job, or retries after a failed attempt
- **THEN** it logs the event at `INFO` or `WARNING` according to severity, without misclassifying it as an unhandled error

#### Scenario: Diagnostic detail is available
- **WHEN** deeper troubleshooting information is emitted for queue contents, path choices, or API request stages
- **THEN** that detail is logged at `DEBUG` so normal production logs remain readable at the default level

