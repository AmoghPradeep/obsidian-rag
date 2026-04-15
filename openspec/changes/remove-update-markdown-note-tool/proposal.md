## Why

The `update_markdown_note` MCP tool has been deemed inconsistent with the intended product design. Keeping a mutating MCP tool exposed expands the server surface area, increases client expectations around write behavior, and conflicts with the desired read-only retrieval role of the MCP server.

## What Changes

- **BREAKING** Remove `update_markdown_note` from the MCP server's advertised tool list.
- **BREAKING** Remove runtime handling and input schema registration for `update_markdown_note`.
- Keep `query_vault_context` as the only MCP tool exposed by the server.
- Remove tests and documentation that describe `update_markdown_note` as part of the supported MCP contract.
- Remove note-update implementation code from the MCP tool layer if it is no longer used anywhere else.

## Capabilities

### New Capabilities
- `mcp-context-retrieval`: Defines the MCP server as a read-only retrieval surface that exposes only `query_vault_context` and returns ranked vault context chunks with provenance metadata.

### Modified Capabilities

## Impact

- Affected code: `src/total_recall/mcp_server/server.py`, `src/total_recall/mcp_server/tools.py`, MCP-related tests, and user-facing docs.
- API impact: MCP clients relying on `update_markdown_note` will break and must stop invoking it.
- Operational impact: the MCP server becomes a smaller read-only interface with less mutation risk.
