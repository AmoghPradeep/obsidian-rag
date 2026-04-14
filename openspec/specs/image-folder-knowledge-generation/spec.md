# image-folder-knowledge-generation Specification

## Purpose
TBD - created by archiving change linux-first-and-image-folder-ingestion. Update Purpose after archive.
## Requirements
### Requirement: Folder-scoped image document ingestion
The system SHALL treat each immediate child directory inside the configured image watch root as one logical source document and MUST generate at most one markdown note per source directory version.

#### Scenario: Multi-image export is grouped into one job
- **WHEN** a watched directory contains multiple supported image files for one exported note
- **THEN** the system MUST process the directory as a single ingestion job instead of one job per image

#### Scenario: Empty or invalid directory is rejected
- **WHEN** a watched directory contains no supported image files
- **THEN** the system MUST return a job error and MUST NOT create a markdown note

### Requirement: Ordered page extraction for image folders
The system SHALL process supported image files in deterministic page order and MUST combine their extracted content into one normalized markdown document.

#### Scenario: Numbered page images are ordered naturally
- **WHEN** a directory contains files such as `image-1-of-3.png`, `image-2-of-3.png`, and `image-10-of-10.png`
- **THEN** the system MUST order pages by natural numeric filename order before transcription

#### Scenario: Shared multimodal pipeline is reused
- **WHEN** the system ingests a folder of page images
- **THEN** it MUST use the same page transcription, reduction, tagging, and markdown-normalization flow used by the PDF image-sequence pipeline

### Requirement: Stable directory completion and idempotency
The system SHALL wait until a watched image directory is stable before processing, and MUST use a directory-level fingerprint so reprocessing occurs only when folder contents change.

#### Scenario: Incomplete copy is deferred
- **WHEN** files inside a watched image directory are still being added or modified during the stability window
- **THEN** the system MUST defer ingestion until the directory contents stop changing

#### Scenario: Directory is reprocessed after content change
- **WHEN** a previously processed directory gains, loses, or changes one of its member image files
- **THEN** the system MUST treat the directory as a new source version and regenerate the markdown output and index entries

### Requirement: Image-folder output participates in existing retrieval flows
The markdown note produced from an image folder SHALL be written into the vault and MUST be chunked, embedded, tagged, and indexed like other generated knowledge documents.

#### Scenario: Successful folder ingestion produces retrievable content
- **WHEN** the system successfully ingests an image folder
- **THEN** it MUST write one markdown note to the vault and update vector storage so MCP retrieval can return the generated content

