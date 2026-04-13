## Context

The project currently exposes tool-like behavior through a custom JSON-over-stdin loop. Core business logic for retrieval and note update exists, but server behavior is not fully MCP protocol compliant for tool discovery, schema advertisement, invocation semantics, and standardized error handling. This blocks smooth interoperability with external MCP clients and makes integration behavior ambiguous.

## Goals / Non-Goals

**Goals:**
- Implement a standards-compliant MCP server runtime surface for this project.
- Register and expose exactly two MCP tools through MCP-native schemas:
  - `query_vault_context`
  - `update_markdown_note`
- Preserve existing business logic where feasible while routing through MCP-compliant handlers.
- Define deterministic argument validation and error/result payload behavior.
- Add protocol-level integration tests for tool listing and invocation behavior.

**Non-Goals:**
- Redesigning vector store internals or embedding model strategy.
- Expanding tool set beyond retrieval and active note update.
- Building non-MCP network transports beyond the selected initial MCP transport.

## Decisions

1. Use MCP SDK/server primitives as the canonical server entrypoint.
- Rationale: avoids custom protocol drift and ensures compatibility with MCP clients.
- Alternative considered: continuing custom stdin JSON wrapper. Rejected due to protocol mismatch risk.

2. Register tools with explicit input schemas and strict validation.
- Rationale: tool contracts must be machine-discoverable and predictable.
- Alternative considered: permissive dynamic args dict parsing. Rejected due to poor client interoperability.

3. Keep retrieval and note-update business logic in `mcp_server/tools.py`, separate from protocol adapter.
- Rationale: isolates protocol plumbing from domain behavior and simplifies testing.
- Alternative considered: embedding all business logic inside MCP handler decorators. Rejected for maintainability.

4. Ambiguity-safe note update behavior.
- Rationale: fuzzy + LLM-guided resolution can be uncertain; unsafe mutation must be prevented.
- Required behavior: if confidence below threshold, return candidate list and no mutation.
- Alternative considered: always choose top candidate. Rejected due to accidental edits risk.

5. Deterministic response envelopes for both tools.
- Rationale: downstream clients need stable parsing for UI/agent workflows.
- Alternative considered: free-form textual responses. Rejected for automation fragility.

6. Protocol-focused test suite.
- Rationale: compliance and interop regressions should be caught early.
- Alternative considered: only unit tests of business logic. Rejected because transport/schema regressions would go undetected.

## Risks / Trade-offs

- [MCP SDK behavior divergence across versions] -> Mitigation: pin compatible MCP dependency version and include transport-level smoke tests.
- [Breaking existing custom clients] -> Mitigation: add migration notes and optionally retain temporary compatibility shim behind flag.
- [Fuzzy resolution causes false positives] -> Mitigation: enforce confidence threshold and ambiguity no-op branch.
- [Schema drift between docs and runtime] -> Mitigation: schema assertions in tests and centralized tool contract definitions.

## Migration Plan

1. Introduce MCP SDK-based server bootstrap and tool registration layer.
2. Map existing `query_vault_context` and `update_markdown_note` logic into MCP handlers.
3. Add validation/error mapping and deterministic result payloads.
4. Run protocol-level tests for discovery and invocation.
5. Remove or deprecate custom JSON-loop path after validation.

## Open Questions

- Which initial MCP transport(s) to prioritize in v1 (stdio only vs stdio + streamable HTTP)?
- Whether to keep temporary compatibility mode for legacy custom JSON clients.
