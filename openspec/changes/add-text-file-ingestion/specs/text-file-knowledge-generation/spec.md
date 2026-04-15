## ADDED Requirements

### Requirement: Watch text drop folders for supported files
The system SHALL watch a configured text-input directory and MUST enqueue stable `.txt` and `.md` files as text-ingestion jobs.

#### Scenario: Detect new plain-text file
- **WHEN** a new stable `.txt` file is written to the configured text watch folder
- **THEN** the system MUST enqueue one text-ingestion job for that file version

#### Scenario: Detect new markdown source file
- **WHEN** a new stable `.md` file is written to the configured text watch folder
- **THEN** the system MUST enqueue one text-ingestion job for that file version

### Requirement: Normalize text files into Obsidian markdown
The system SHALL read the source text content and MUST generate a normalized Obsidian markdown note through the same prompt-to-JSON style used by existing text-producing ingestion flows.

#### Scenario: Plain-text source is normalized
- **WHEN** a queued `.txt` ingestion job runs successfully
- **THEN** the system MUST read the text, invoke markdown normalization, write one markdown note into the vault, and persist generated tags

#### Scenario: Markdown source is normalized rather than copied verbatim
- **WHEN** a queued `.md` ingestion job runs successfully
- **THEN** the system MUST treat the file contents as source material for normalization and MUST write a vault markdown note using the standard generated-note flow

### Requirement: Preserve provenance for imported text sources
The system SHALL preserve a raw copy of each ingested text source under the vault raw-data area and MUST keep the generated note traceable to that source.

#### Scenario: Raw text source is copied into vault storage
- **WHEN** a text-ingestion job is prepared for processing
- **THEN** the system MUST copy the source file into `z.rawdata/text/` using the same source-preparation model used by other file-based jobs

#### Scenario: Generated note includes source provenance
- **WHEN** text markdown generation completes successfully
- **THEN** the resulting note MUST retain provenance to the raw imported source file

### Requirement: Text-ingestion output participates in retrieval
The markdown note produced from a text source SHALL be written into the vault and MUST be chunked, embedded, tagged, and indexed like other generated knowledge documents.

#### Scenario: Successful text ingestion produces retrievable content
- **WHEN** the system successfully ingests a `.txt` or `.md` source file
- **THEN** it MUST write a vault markdown note and update vector storage so retrieval can return the generated content

### Requirement: Text ingestion respects existing idempotency and stability rules
The system SHALL defer unstable text files and MUST avoid duplicate processing for an unchanged source file version.

#### Scenario: Incomplete text file copy is deferred
- **WHEN** a watched `.txt` or `.md` file is still changing during the stability window
- **THEN** the system MUST defer ingestion until the file becomes stable

#### Scenario: Unchanged text file is not duplicated
- **WHEN** duplicate watcher events occur for the same unchanged `.txt` or `.md` source version
- **THEN** the system MUST avoid creating duplicate jobs or duplicate indexed output
