## Context

The current MCP server exposes two tools: `query_vault_context` and `update_markdown_note`. The desired direction is narrower: the MCP server should serve only retrieval use cases, while note mutation should no longer be part of the public MCP contract. The implementation currently wires note-update behavior into tool discovery, request validation, invocation dispatch, tests, and documentation.

## Goals / Non-Goals

**Goals:**
- Reduce the MCP server to a single exposed tool: `query_vault_context`.
- Remove all protocol-visible references to `update_markdown_note`.
- Remove note-update code from the MCP tool layer if it has no remaining callers.
- Update tests and docs so the supported MCP contract is unambiguous.

**Non-Goals:**
- Changing retrieval behavior, ranking logic, or payload structure for `query_vault_context`.
- Redesigning background ingestion, indexing, or non-MCP note processing flows.
- Adding replacement MCP write tools.

## Decisions

1. Remove `update_markdown_note` from `tool_definitions()` and from request dispatch.
Rationale: MCP discovery must reflect the intended public contract. Leaving a deprecated tool in discovery creates incompatible client behavior.
Alternative considered: keep the tool listed but return a deprecation error. Rejected because the design target is a single-tool server, not a transitional dual-tool contract.

2. Delete the `UpdateMarkdownNoteInput` schema and related validation path.
Rationale: once the tool is removed, retaining dead schema code increases maintenance cost and obscures the actual MCP API.
Alternative considered: keep the schema for possible future restoration. Rejected because OpenSpec should describe the current design, not speculative reuse.

3. Remove `MCPTools.update_markdown_note()` and its helper methods if they are unused after server changes.
Rationale: the user asked for safe removal, which means reducing dead code rather than only hiding it from `tools/list`.
Alternative considered: keep the implementation as an internal helper. Rejected unless another in-repo caller still depends on it.

4. Tighten tests around single-tool behavior.
Rationale: the regression risk is primarily contract drift. Tests should assert that `tools/list` contains only `query_vault_context` and that calling `update_markdown_note` now yields a tool-not-found error.
Alternative considered: only updating existing happy-path tests. Rejected because it would not protect the removed behavior boundary.

## Risks / Trade-offs

- [Existing MCP clients still call `update_markdown_note`] -> Mitigation: document the removal as a breaking change and return `Tool not found` consistently.
- [Removing the tool implementation breaks an unseen internal caller] -> Mitigation: search the repo before deletion and preserve only code with confirmed non-MCP callers.
- [Tests continue to encode the old two-tool contract] -> Mitigation: rewrite tool-list and invocation assertions to enforce the single-tool surface.

## Migration Plan

1. Remove `update_markdown_note` from MCP tool registration, schema definitions, and dispatch logic.
2. Search for remaining call sites and delete the note-update implementation/helpers if unused.
3. Update MCP protocol and integration tests to assert single-tool behavior and unknown-tool errors for `update_markdown_note`.
4. Update README and other user-facing references to describe the MCP server as retrieval-only.

## Open Questions

None.
