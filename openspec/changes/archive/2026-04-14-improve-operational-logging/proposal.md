## Why

The system has basic logging, but many critical execution paths still fail with too little context or with inconsistent severity. That makes it hard to diagnose ingestion problems, retry behavior, API failures, and indexing errors during real operations.

## What Changes

- Add more comprehensive logging across background ingestion, MCP flows, API client calls, queue processing, and indexing.
- Ensure failure points emit actionable context such as job type, source path, attempt number, and operation stage.
- Standardize log levels so routine progress uses `INFO`, noisy execution details use `DEBUG`, recoverable issues use `WARNING`, and exception catches emit `ERROR` or `exception()` logs.
- Improve exception-path logging so every caught error records enough context to support debugging without reproducing the issue blindly.
- Update tests to validate key logging behavior where practical.

## Capabilities

### New Capabilities
- `operational-logging-and-failure-observability`: Emit consistent, contextual logs across normal execution, retries, and failure paths so operators can diagnose issues quickly.

### Modified Capabilities
- None.

## Impact

- Affected code: background worker pipelines, watchers, queue processing, MCP tool flows, API client wrappers, and logging setup.
- Affected systems: operators and service owners get better observability during local runs and long-lived service deployments.
- Dependencies: no new runtime dependency is required if the change stays within the standard logging library.
