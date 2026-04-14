## Context

The repository already initializes Python logging globally and emits some `INFO`, `WARNING`, and exception logs in a few worker modules. The problem is not the absence of logging entirely, but the lack of comprehensive, structured coverage across the most failure-prone paths: scan and enqueue decisions, job preparation, retry loops, API failures, markdown write failures, indexing failures, and MCP tool execution. Several exception handlers log generic messages without enough surrounding context to explain what the system was doing when the failure occurred.

This is a cross-cutting operational change because consistent logging has to span multiple modules rather than being fixed in one pipeline. It also needs level discipline so the service remains readable in production instead of becoming noisy.

## Goals / Non-Goals

**Goals:**
- Add contextual logs at important execution stages for ingestion, indexing, and MCP operations.
- Ensure every exception catch logs the failure with useful identifying context.
- Standardize severity usage across debug, info, warning, and error paths.
- Improve retry and skip-path visibility so operators can tell whether work was processed, deferred, retried, skipped, or failed.

**Non-Goals:**
- Introducing a third-party observability stack, tracing system, or metrics backend.
- Logging sensitive file contents, full prompts, or credentials.
- Reworking business logic beyond what is needed to expose better logs.

## Decisions

1. Keep the standard `logging` module and improve message quality instead of introducing a new logging framework.
- Rationale: the repo already uses Python logging and does not need a dependency jump to solve the current observability gap.
- Alternative considered: add structured-logging libraries. Rejected because the immediate need is coverage and consistency, not a new serialization format.

2. Log operation boundaries and decisions, not only failures.
- Rationale: many debugging sessions depend on knowing whether a file was discovered, deferred, skipped as duplicate, copied, retried, indexed, or written successfully.
- Approach: add `INFO` logs for major state transitions, `DEBUG` logs for lower-level details, and `WARNING` logs for recoverable anomalies.
- Alternative considered: log only exceptions. Rejected because it still leaves operators blind to silent skips and retry behavior.

3. Every `except` block must record contextual identifiers with `LOG.exception(...)` or an equivalent error log.
- Rationale: generic failure messages force operators to reproduce issues manually.
- Approach: include operation name plus identifiers like job type, source path, output path, attempt number, or tool name.
- Alternative considered: rely on outer-layer logs only. Rejected because important context is often only available at the catch site.

4. Avoid logging sensitive payloads or large model inputs.
- Rationale: prompts, note contents, and credentials may contain private user data.
- Approach: log identifiers, counts, and stage names rather than raw note content or full prompts.
- Alternative considered: log full inputs for easier debugging. Rejected because it creates unnecessary privacy and noise risks.

## Risks / Trade-offs

- [Extra logs make service output noisy] -> Mitigation: reserve `DEBUG` for chatty detail and keep `INFO` focused on stage transitions and outcomes.
- [Contextual logs accidentally expose sensitive content] -> Mitigation: log file paths, counts, and IDs instead of prompts, transcripts, or note bodies.
- [Inconsistent adoption across modules leaves gaps] -> Mitigation: audit the main worker, pipeline, client, and MCP modules as part of implementation.
- [Tests become brittle if they assert exact strings too aggressively] -> Mitigation: validate presence of key contextual fields and severity intent rather than full log text.

## Migration Plan

1. Audit the current logging and exception-catching surface.
2. Add boundary, decision, retry, and failure logs in the worker and pipeline modules.
3. Improve API client and MCP logging around failures and recovery paths.
4. Update tests to cover representative logging behavior.
5. Review runtime output to confirm the logs are more actionable without leaking sensitive content.

## Open Questions

- None. The need is broader and more consistent logging coverage using the existing logging stack.
