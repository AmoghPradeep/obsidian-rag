## ADDED Requirements

### Requirement: Expose only the vault context query tool
The MCP server SHALL expose `query_vault_context` as its only tool and SHALL NOT advertise note-mutation tools.

#### Scenario: Tool discovery returns a single tool
- **WHEN** an MCP client invokes `tools/list`
- **THEN** the server returns exactly one tool definition named `query_vault_context`

#### Scenario: Removed tool is not discoverable
- **WHEN** an MCP client inspects the advertised MCP tool definitions
- **THEN** no tool named `update_markdown_note` is present

### Requirement: Reject removed tool invocations
The MCP server SHALL reject invocations for MCP tools that are no longer part of the supported contract.

#### Scenario: Removed note-update tool is called
- **WHEN** an MCP client invokes `tools/call` with `name` equal to `update_markdown_note`
- **THEN** the server returns a tool-not-found error

### Requirement: Provide retrieval schema and ranked results
The MCP server SHALL validate and execute `query_vault_context` with a stable retrieval contract.

#### Scenario: Retrieval schema is advertised
- **WHEN** an MCP client inspects `query_vault_context`
- **THEN** the tool schema includes required query text and optional bounded `k`

#### Scenario: Retrieval returns ranked context with provenance
- **WHEN** `query_vault_context` executes successfully
- **THEN** the response includes up to `k` ranked chunks with content, document path, chunk identifier, and similarity metadata
