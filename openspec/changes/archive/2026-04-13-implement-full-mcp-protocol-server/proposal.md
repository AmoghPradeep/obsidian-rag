## Why

The current MCP entrypoint is a custom JSON-over-stdin loop, which is useful for local testing but not a full MCP protocol implementation. Implementing a standards-compliant MCP server now is necessary for reliable interoperability with MCP clients and tool ecosystems.

## What Changes

- Replace the ad-hoc stdio JSON loop with a protocol-compliant MCP server runtime and lifecycle.
- Implement proper MCP tool registration and schema-exposed contracts for:
  - `query_vault_context`
  - `update_markdown_note`
- Implement MCP-compliant request/response handling, errors, and capability advertisement.
- Add protocol-level validation tests for tool discovery, invocation, argument validation, and error semantics.
- Keep existing business logic for retrieval and note update tools, but route calls through MCP-compliant handlers.

## Capabilities

### New Capabilities
- `mcp-protocol-server`: Run a standards-compliant MCP server transport with capability advertisement, tool discovery, invocation, and error handling.
- `mcp-tool-contracts`: Expose retrieval and note-update tools with explicit MCP schemas and deterministic result/error payloads.
- `foreground-note-update-tool`: Provide a client-invoked MCP tool that resolves and updates user-referenced markdown notes (summary/tags/path/reindex).

### Modified Capabilities
- None.

## Impact

- Affected code: `mcp_server/server.py`, `mcp_server/tools.py`, transport/bootstrap wiring, tool schema definitions, and tests.
- APIs: MCP client-facing protocol behavior (tool listing/invocation/validation/errors) becomes standards-compliant.
- Dependencies/systems: MCP SDK/runtime usage becomes mandatory for server entrypoint behavior.
- Operational impact: Improved compatibility with external MCP clients and lower integration ambiguity.
