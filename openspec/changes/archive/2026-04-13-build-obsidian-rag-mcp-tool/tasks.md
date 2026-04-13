## 1. Project Skeleton and Configuration

- [x] 1.1 Create Python package structure for `background_worker`, `mcp_server`, and shared `rag_core` modules
- [x] 1.2 Add runtime dependencies for file watching, MCP server SDK, embeddings, vector store adapter, and PDF/audio processing
- [x] 1.3 Implement typed configuration loader for vault path, watched folders, model IDs, chunking settings, and vector backend
- [x] 1.4 Add structured logging and common error/result types used across ingestion and MCP tools
- [x] 1.5 Set default model config values: `cohere-transcribe-03-2026`, `gemma4-26B-A4B` (`Q3_K_M`), and `Qwen3-Embedding-0.6B`

## 2. Core RAG Indexing Components

- [x] 2.1 Implement markdown normalizer contract (frontmatter + canonical sections) for generated and vault markdown
- [x] 2.2 Implement chunking pipeline with configurable chunk size/overlap and stable chunk IDs
- [x] 2.3 Implement embedding service wrapper with retry/backoff and batch support
- [x] 2.4 Implement `VectorStore` interface and initial local backend adapter (including upsert, delete-by-doc, and query)

## 3. Background Knowledge Generation (Audio/PDF)

- [x] 3.1 Implement Windows-compatible folder watchers with stable-file detection and enqueue semantics
- [x] 3.2 Implement durable ingestion queue and idempotency key generation for source file versions
- [x] 3.3 Implement OpenAI-first runtime policy with optional OpenAI-compatible endpoint fallback and local lifecycle cleanup hooks
- [x] 3.4 Implement audio pipeline: preprocess/compress `.m4a` -> OpenAI-first transcription (optional local ASR) -> prompt-to-JSON markdown normalization -> vault write
- [x] 3.5 Implement PDF pipeline: `pdf -> jpg` conversion, page-level multimodal extraction, map-reduce summary generation, and vault write
- [x] 3.6 Chain post-generation indexing for both pipelines (chunk, embed, vector upsert) with provenance metadata
- [x] 3.7 Implement domain-tag generation with catalog reuse policy, new-tag gating, and DB persistence of tag assignments
- [x] 3.8 Add failure handling, retries, and guaranteed model ejection in all error paths

## 4. Foreground Knowledge Generation MCP Tool

- [x] 4.1 Define MCP tool contract for `reindex_vault_delta` with validation and result schema
- [x] 4.2 Implement vault markdown scanner and fingerprint manifest persistence/load on startup
- [x] 4.3 Implement delta planner for new/changed/deleted markdown files
- [x] 4.4 Implement delta execution to re-embed changed/new files and delete vectors for removed files
- [x] 4.5 Return deterministic summary metrics (processed, skipped, deleted, errors) from tool responses

## 5. MCP Context Retrieval Tool

- [x] 5.1 Define MCP tool contract for `query_vault_context` with query text and `k` (no metadata filters in v1)
- [x] 5.2 Implement retrieval service that validates/clamps `k` and executes vector similarity search
- [x] 5.3 Format response payload with ranked chunks, scores, source file path, and chunk identifiers

## 6. Startup, Packaging, and Validation

- [x] 6.1 Add Windows startup integration script (Task Scheduler registration) for background worker
- [x] 6.2 Add CLI entrypoints for background worker and MCP server processes
- [x] 6.3 Add unit tests for chunking, idempotency, manifest delta detection, and retrieval validation rules
- [x] 6.4 Add integration tests for end-to-end audio/PDF ingestion and MCP reindex/query flows with local fixtures
- [x] 6.5 Document runbook for configuration, startup setup, and recovery/rebuild steps

## 7. Vault Path Safety Hardening

- [x] 7.1 Implement a sanitizer for LLM-proposed `relativePath` that rejects absolute/rooted paths and normalizes separators/segments
- [x] 7.2 Enforce vault-root containment check before markdown writes and block malformed folder creation (for example `C--Users...`)
- [x] 7.3 Add fallback destination policy for invalid LLM paths with warning/error logging
- [x] 7.4 Add unit/integration tests for absolute paths, traversal segments, malformed windows-style paths, and safe fallback behavior
- [x] 7.5 Harden markdown-generation system prompt to require vault-relative `relativePath` and explicitly forbid absolute/traversal forms
- [x] 7.6 Add prompt-regression tests to verify path constraints remain present and parser-compatible

## 8. Operator Config and Restart UX

- [x] 8.1 Set default env config path to `C:\Users\<current_user>\.obragconfig\.env` and enable nested env parsing with `__`
- [x] 8.2 Document startup-operator workflow for editing `.obragconfig\.env` and restarting scheduled background task
- [x] 8.3 Document explicit restart commands (`schtasks /End` and `schtasks /Run`) and startup-only config loading behavior

## 9. PDF Pipeline Hardening and Efficiency

- [x] 9.1 Implement true multimodal PDF page requests so image payloads are actually sent to model APIs
- [x] 9.2 Enforce OpenAI-first PDF routing with local OpenAI-compatible fallback only on OpenAI failure
- [x] 9.3 Remove silent placeholder behavior for PDF extraction when both providers fail and return explicit job errors
- [x] 9.4 Add grayscale + moderate compression preprocessing for rendered page images with readability-preserving defaults
- [x] 9.5 Copy source PDFs into vault `z.rawdata/pdf/` and include backlinks to copied files in generated markdown
- [x] 9.6 Move rendered PDF images to temp-only storage and ensure cleanup on success/failure
- [x] 9.7 Consolidate PDF prompts into `system_prompts.py` and remove inline prompt strings from `pdf_pipeline.py`
- [x] 9.8 Add tests for multimodal payload usage, provider fallback order, raw PDF backlink correctness, temp cleanup, and compression settings

## 10. MCP Foreground Active Note Update

- [x] 10.1 Define MCP tool contract `update_markdown_note` with input fields for note reference text and update context
- [x] 10.2 Implement fuzzy candidate search over vault markdown paths/names for non-exact note references
- [x] 10.3 Implement LLM-guided candidate resolution with confidence scoring and ambiguity-safe no-op response
- [x] 10.4 Implement note mutation logic that preserves original content and adds/refreshes managed `Summary` and `Tags` sections only
- [x] 10.5 Implement destination path recommendation and safe vault-relative move with containment checks
- [x] 10.6 Implement vector reindex for updated note and stale-vector removal when note path changes
- [x] 10.7 Return deterministic MCP output payload including resolved file, confidence, changes applied, and old/new path metadata
- [x] 10.8 Add unit/integration tests for fuzzy matching, ambiguity behavior, content preservation, section updates, path relocation, and reindex side effects
