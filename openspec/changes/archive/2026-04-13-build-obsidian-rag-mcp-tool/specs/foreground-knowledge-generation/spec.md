## ADDED Requirements

### Requirement: Expose MCP active markdown update tool
The system SHALL expose an MCP tool that updates a user-referenced markdown note in the vault while preserving original content.

#### Scenario: Update note by fuzzy reference
- **WHEN** `update_markdown_note` is invoked with a note reference that is not an exact file name
- **THEN** the system performs fuzzy candidate selection and LLM-guided resolution to choose the most relevant vault markdown file

#### Scenario: Preserve original note content
- **WHEN** target note is selected for update
- **THEN** the system preserves existing note body content and only adds/refreshes managed sections (`Summary`, `Tags`)

### Requirement: Relocate note to appropriate vault path safely
The system SHALL move the updated note to the most appropriate vault-relative path when relocation is recommended.

#### Scenario: Safe path relocation
- **WHEN** update flow determines a better destination path
- **THEN** the system applies vault-safe path validation, moves the note, and reports old/new paths in tool output

### Requirement: Reindex affected vectors after note update/move
The system SHALL refresh vector index entries for the updated note and delete stale entries tied to the old path when moved.

#### Scenario: Reindex updated note
- **WHEN** `update_markdown_note` completes content/path updates
- **THEN** the system recomputes chunks/embeddings for the final note and upserts vectors to vector store

#### Scenario: Remove stale vectors after move
- **WHEN** note path changes during update
- **THEN** the system removes vectors associated with the previous path

### Requirement: Handle ambiguity without unsafe mutation
The system SHALL avoid updating files when note resolution confidence is low.

#### Scenario: Ambiguous note reference
- **WHEN** multiple candidate notes are plausible and confidence threshold is not met
- **THEN** the tool returns candidate options and performs no file mutation
