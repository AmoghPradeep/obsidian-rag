## 1. Logging Audit and Standards

- [x] 1.1 Audit current logs and exception catches across worker, pipeline, MCP, and API client modules
- [x] 1.2 Define consistent severity usage for lifecycle, debug, warning, retry, and exception paths
- [x] 1.3 Identify sensitive fields that must not be logged and apply that constraint to implementation

## 2. Background Worker and Pipeline Coverage

- [x] 2.1 Add contextual logs around watcher scans, enqueue decisions, deferrals, and duplicate or skip cases
- [x] 2.2 Add start, success, retry, and failure logs around job preparation, execution, markdown writing, and indexing
- [x] 2.3 Update exception catches in audio, PDF, image-folder, and markdown-processing flows to emit error logs with source context

## 3. API and MCP Coverage

- [x] 3.1 Add contextual logging around generation, transcription, and embedding API failure points without logging sensitive payloads
- [x] 3.2 Add logs for MCP tool execution boundaries, candidate resolution, updates, and failure paths
- [x] 3.3 Ensure retryable or recoverable issues are logged at warning-level and diagnostic details are available at debug-level

## 4. Validation

- [x] 4.1 Add or update tests that verify representative logging behavior and exception-path coverage
- [x] 4.2 Run the relevant test suite and review runtime output to confirm the new logs are actionable and not excessively noisy
