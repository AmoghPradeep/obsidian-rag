# MCP Migration Notes

## Summary

The MCP server no longer accepts the legacy custom line-JSON tool format:

```json
{"tool":"query_vault_context","args":{"query":"...","k":5}}
```

Use MCP JSON-RPC over stdio instead.

## Required Request Sequence

1. Call `initialize`.
2. Call `tools/list` to discover tool contracts.
3. Call `tools/call` with `name` and `arguments`.

## Tool Names

- `query_vault_context`

## Example

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"query_vault_context","arguments":{"query":"meeting notes","k":5}}}
```

## Error Contract

- Invalid arguments return JSON-RPC error code `-32602`.
- Unknown tools/methods return `-32601`.
- Tool runtime failures return `-32000` with non-sensitive error data (`tool`, `type`).
