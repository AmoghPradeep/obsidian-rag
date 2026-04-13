## ADDED Requirements

### Requirement: Expose MCP semantic context query tool
The system SHALL expose an MCP tool that accepts a natural-language query and returns top-k relevant knowledge chunks from the Obsidian vector index.

#### Scenario: Return ranked context chunks
- **WHEN** `query_vault_context` is invoked with query text and `k`
- **THEN** the system returns up to `k` chunks ranked by vector similarity score

#### Scenario: Respect retrieval limits
- **WHEN** `query_vault_context` is invoked with `k` outside configured bounds
- **THEN** the system clamps or rejects the value according to configured policy and reports validation behavior

#### Scenario: Retrieval executes without metadata filters
- **WHEN** `query_vault_context` is invoked in v1
- **THEN** the system performs pure embedding similarity search over indexed chunks without metadata-filter parameters

### Requirement: Include source metadata in retrieval results
The system SHALL return provenance metadata for each retrieved chunk.

#### Scenario: Include chunk provenance
- **WHEN** chunks are returned for a query
- **THEN** each chunk includes source markdown path, chunk identifier, and similarity score
