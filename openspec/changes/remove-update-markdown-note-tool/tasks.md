## 1. MCP Surface Reduction

- [x] 1.1 Remove `update_markdown_note` schema registration, tool definition, and dispatch handling from the MCP server runtime.
- [x] 1.2 Remove `update_markdown_note` implementation and helper code from `mcp_server/tools.py` if no non-MCP callers remain.

## 2. Contract Verification

- [x] 2.1 Update MCP protocol and integration tests to assert that `tools/list` exposes only `query_vault_context`.
- [x] 2.2 Add or update a test that `tools/call` for `update_markdown_note` returns a tool-not-found error.

## 3. Documentation

- [x] 3.1 Update README and any MCP-facing documentation to describe the server as retrieval-only.
