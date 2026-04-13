## 1. MCP Server Runtime

- [x] 1.1 Replace custom stdin JSON loop with MCP SDK/server bootstrap entrypoint
- [x] 1.2 Implement MCP capability advertisement and tool listing behavior
- [x] 1.3 Add structured MCP error mapping for validation and runtime failures

## 2. MCP Tool Contracts

- [x] 2.1 Define explicit MCP input schemas for `query_vault_context` and `update_markdown_note`
- [x] 2.2 Implement schema-based argument validation before tool execution
- [x] 2.3 Ensure deterministic JSON-serializable success payloads for both tools

## 3. Foreground Note Update Integration

- [x] 3.1 Integrate fuzzy+LLM note resolution path into MCP handler with confidence threshold enforcement
- [x] 3.2 Enforce ambiguity-safe no-op response contract when confidence is below threshold
- [x] 3.3 Wire note mutation, safe move, and reindex cleanup into MCP tool transaction flow

## 4. Testing and Migration

- [x] 4.1 Add protocol-level tests for MCP tool discovery and invocation
- [x] 4.2 Add validation/error contract tests for malformed arguments and handler exceptions
- [x] 4.3 Add end-to-end tests for `update_markdown_note` MCP invocation success and ambiguity branches
- [x] 4.4 Document migration notes for clients moving from custom JSON loop to MCP protocol runtime
