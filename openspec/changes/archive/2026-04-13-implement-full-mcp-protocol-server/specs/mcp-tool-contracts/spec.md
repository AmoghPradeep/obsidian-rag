## ADDED Requirements

### Requirement: Register retrieval and note-update tools with explicit schemas
The system SHALL register `query_vault_context` and `update_markdown_note` as MCP tools with explicit, stable input contracts.

#### Scenario: Retrieval tool schema availability
- **WHEN** an MCP client inspects `query_vault_context`
- **THEN** the schema includes required query text and optional bounded `k` argument

#### Scenario: Note update tool schema availability
- **WHEN** an MCP client inspects `update_markdown_note`
- **THEN** the schema includes required note reference input and optional update context fields

### Requirement: Return deterministic tool outputs
The system SHALL return deterministic JSON-serializable output payloads for both tools.

#### Scenario: Retrieval result payload shape
- **WHEN** `query_vault_context` executes successfully
- **THEN** response includes top-k chunk contents with source metadata and similarity score fields

#### Scenario: Note update result payload shape
- **WHEN** `update_markdown_note` executes successfully
- **THEN** response includes status, resolved file path, confidence, mutation flags, and old/new path metadata
