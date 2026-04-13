## ADDED Requirements

### Requirement: Resolve note targets safely from fuzzy user references
The system SHALL resolve a user-referenced markdown note via fuzzy candidate search and LLM-guided selection.

#### Scenario: High-confidence target selection
- **WHEN** note reference maps to a high-confidence candidate
- **THEN** the tool selects that note for update

#### Scenario: Ambiguous target no-op
- **WHEN** confidence threshold is not met
- **THEN** the tool returns candidate options and performs no file mutation

### Requirement: Preserve original content while updating managed sections
The system SHALL preserve existing note body content and only add/refresh managed `Summary` and `Tags` sections.

#### Scenario: Section refresh without body overwrite
- **WHEN** note update is applied
- **THEN** original note body remains intact while managed sections are created or updated

### Requirement: Safe relocation and reindex after update
The system SHALL support vault-safe relocation of updated notes and refresh vector index state accordingly.

#### Scenario: Move note to recommended path
- **WHEN** relocation is recommended
- **THEN** note is moved to a validated vault-relative path and response includes old/new paths

#### Scenario: Reindex and stale-vector cleanup
- **WHEN** note update or move completes
- **THEN** vectors for final note path are upserted and stale vectors for old path are removed when applicable
