## ADDED Requirements

### Requirement: Watch audio and PDF drop folders
The system SHALL run a Windows-startup background process that watches configured audio and PDF folders for new supported files.

#### Scenario: Detect new audio file
- **WHEN** a new `.m4a` file is written to the configured audio folder
- **THEN** the system enqueues an audio ingestion job exactly once for that file version

#### Scenario: Detect new PDF file
- **WHEN** a new `.pdf` file is written to the configured PDF folder
- **THEN** the system enqueues a PDF ingestion job exactly once for that file version

### Requirement: Process audio files into normalized Obsidian markdown
The system SHALL preprocess each queued audio file, transcribe it, normalize the transcript into Obsidian markdown through an LLM prompt-to-JSON flow, and write the markdown document to the vault.

#### Scenario: Successful audio ingestion
- **WHEN** an audio job starts for a stable `.m4a` file
- **THEN** the system compresses/preprocesses audio, transcribes it, generates normalized markdown + tags via LLM response, writes markdown to vault, and persists tags to the tag catalog/database

#### Scenario: Audio ingestion failure cleanup
- **WHEN** audio transcription or normalization fails
- **THEN** the system records an error status for the job, cleans up runtime state, and retries or terminates according to policy

### Requirement: Use OpenAI APIs as primary transcription and generation path
The system SHALL use OpenAI APIs as the primary path for transcription and generation in the audio workflow.

#### Scenario: OpenAI-first transcription
- **WHEN** an audio ingestion job runs with `transcribe_local` disabled
- **THEN** the system transcribes audio with OpenAI transcription API and continues with OpenAI-first generation flow

#### Scenario: OpenAI-first generation
- **WHEN** transcript normalization runs
- **THEN** the system prefers OpenAI API generation and only uses OpenAI-compatible endpoint fallback when configured/required

### Requirement: Support optional local transformer ASR fallback
The system SHALL support a local transcription mode controlled by configuration for cases where OpenAI transcription is not used.

#### Scenario: Local transcription enabled
- **WHEN** `transcribe_local` is enabled
- **THEN** the system loads local ASR runtime, transcribes audio locally, and ejects/cleans up runtime per lifecycle policy

### Requirement: Process PDFs into normalized markdown with summary
The system SHALL convert each queued PDF into normalized markdown that includes extracted content and a summary, and persist it to the vault.

#### Scenario: Successful PDF ingestion
- **WHEN** a PDF job starts for a stable `.pdf` file
- **THEN** the system converts PDF pages to images, performs page-level multimodal extraction/normalization, reduces page summaries into a document summary, writes markdown to vault, and ejects the model when locally loaded

#### Scenario: Low-confidence handwritten extraction
- **WHEN** PDF handwritten content cannot be reliably parsed
- **THEN** the system still writes markdown with available extracted text and marks extraction confidence metadata

### Requirement: Route PDF generation through OpenAI-first with local fallback
The system SHALL use OpenAI as the primary provider for PDF page extraction and reduction, with local OpenAI-compatible fallback only when OpenAI requests fail.

#### Scenario: OpenAI-first page extraction
- **WHEN** a page extraction request is issued for PDF processing
- **THEN** the system first calls OpenAI APIs and only uses local OpenAI-compatible endpoint if OpenAI call fails

#### Scenario: Fail after both providers fail
- **WHEN** both OpenAI and local fallback providers fail for a PDF generation step
- **THEN** the PDF job fails with explicit error status and no silent placeholder generation

### Requirement: Perform readability-preserving image optimization
The system SHALL optimize rendered PDF page images for token efficiency using grayscale conversion and moderate compression while preserving small handwritten text legibility.

#### Scenario: Handwritten PDF page optimization
- **WHEN** a PDF page image is prepared for multimodal extraction
- **THEN** the system applies grayscale conversion and non-aggressive compression settings before model call

### Requirement: Preserve raw PDF copy and backlink it in generated markdown
The system SHALL copy each processed source PDF into vault `z.rawdata/pdf/` and include a backlink to that copied file in the generated markdown note.

#### Scenario: Raw PDF copied and linked
- **WHEN** PDF markdown generation completes
- **THEN** markdown includes backlink to the copied raw PDF path under `z.rawdata/pdf/`

### Requirement: Keep rendered page images as temp-only artifacts
The system SHALL store rendered PDF page images in temporary storage and clean them up after job completion or failure.

#### Scenario: Temp image cleanup on completion
- **WHEN** PDF processing succeeds or fails
- **THEN** temporary rendered image files are removed and are not persisted in vault content paths

### Requirement: Centralize and harden PDF prompts
The system SHALL define PDF extraction, reduction, tagging, and markdown-structure prompts in `system_prompts.py` and avoid inline prompt strings in PDF pipeline code.

#### Scenario: Prompt source of truth
- **WHEN** PDF pipeline constructs model inputs
- **THEN** it uses prompt-builder functions from `system_prompts.py` with explicit path/backlink/output constraints

### Requirement: Generate and reuse domain tags during markdown creation
The system SHALL assign knowledge-domain tags during markdown generation, prefer existing tags from a persisted tag catalog, and allow creating a new tag only when no existing tag is suitable.

#### Scenario: Reuse existing tags
- **WHEN** markdown is generated and at least one catalog tag is relevant
- **THEN** the system outputs existing catalog tags in the markdown frontmatter and stores the tag associations in the database

#### Scenario: Create new tag only if necessary
- **WHEN** markdown is generated and no catalog tag is relevant above configured threshold
- **THEN** the system allows the LLM to propose a new domain tag and persists it to the tag catalog for reuse

### Requirement: Enforce vault-relative markdown output paths
The system SHALL sanitize and validate LLM-proposed markdown output paths so the final write target is always a safe path under the configured vault root.

#### Scenario: LLM returns absolute Windows path-like value
- **WHEN** LLM output includes a path resembling an absolute path (for example drive-letter or root-prefixed form)
- **THEN** the system rejects or rewrites it to a safe vault-relative path and does not create malformed folders such as `C--Users...`

#### Scenario: LLM returns traversal segments
- **WHEN** LLM output includes `..` or other traversal-like segments
- **THEN** the system normalizes/collapses the path and enforces vault containment before writing markdown

#### Scenario: Invalid path falls back safely
- **WHEN** proposed path cannot be sanitized into a valid vault-relative destination
- **THEN** the system writes markdown to a configured fallback folder/name inside the vault and records a warning

### Requirement: Constrain `relativePath` in system prompts
The system SHALL harden generation prompts so `relativePath` is specified as vault-relative only and excludes absolute/path-traversal forms.

#### Scenario: Prompt explicitly forbids absolute paths
- **WHEN** the markdown-generation prompt is constructed
- **THEN** prompt instructions explicitly disallow drive-letter paths, root-prefixed paths, UNC paths, and traversal segments

#### Scenario: Prompt and sanitizer operate as defense in depth
- **WHEN** LLM still returns a non-compliant `relativePath`
- **THEN** runtime path sanitizer/validator still prevents out-of-vault or malformed writes

### Requirement: Use operator-accessible startup configuration source
The system SHALL load runtime configuration from an operator-accessible user-home path suitable for Windows startup execution.

#### Scenario: Default user-home env config path
- **WHEN** background worker starts without overriding config source
- **THEN** it reads `.env` from `C:\Users\<current_user>\.obragconfig\.env` using `OBRAG_`-prefixed keys and nested `__` separators

#### Scenario: Config change applied after restart
- **WHEN** an operator modifies values in `.obragconfig\.env`
- **THEN** new values apply only after background process restart and runbook documents restart commands

### Requirement: Index generated markdown into vector store
The system SHALL chunk every generated markdown document, create embeddings, and upsert chunks with source metadata into a vector database.

#### Scenario: Index new generated markdown
- **WHEN** markdown generation succeeds for an audio or PDF source
- **THEN** the system chunks the markdown, computes embeddings, and stores chunk vectors linked to document metadata and source path

#### Scenario: Prevent duplicate indexing for same file version
- **WHEN** duplicate watcher events occur for an unchanged source file version
- **THEN** the system avoids creating duplicate chunk vectors for that source version
