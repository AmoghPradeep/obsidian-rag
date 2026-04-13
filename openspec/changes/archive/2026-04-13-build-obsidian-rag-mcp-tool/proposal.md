## Why

Knowledge in an Obsidian vault is growing from multiple sources (audio notes, scanned/handwritten PDFs, and direct markdown edits), but it is not consistently normalized or retrievable through MCP-native semantic search. Building a Python RAG-based MCP tool now enables always-on ingestion plus low-latency context retrieval for downstream assistants and workflows.

## What Changes

- Add a Windows-startup background ingestion service with filesystem watchers for audio and PDF drop folders.
- Add audio ingestion pipeline for new `.m4a` files: transcription, markdown normalization, vault write, chunking, embedding, and vector upsert.
- Add PDF ingestion pipeline for new `.pdf` files: OCR/text extraction via LLM normalization, summary generation, markdown write, chunking, embedding, and vector upsert.
- Add OpenAI API-first model invocation for transcription and generation, with local/OpenAI-compatible fallback paths where configured.
- Replace the foreground MCP delta-reindex focus with an active note-update MCP tool that resolves a user-referenced markdown note (fuzzy + LLM-guided match), preserves original content, adds/refreshes Summary + Tags sections, and relocates the file to the most appropriate vault path.
- Add an MCP retrieval tool that returns top-`k` relevant chunks from vector storage for a query.
- Add metadata + idempotency model to prevent duplicate processing and enable safe reprocessing when source files change.
- Add robust vault path-safety enforcement for LLM-proposed `relativePath` values to prevent malformed absolute-path-derived folders in the vault.
- Add system-prompt hardening so LLM is explicitly constrained to emit vault-relative `relativePath` values only.
- Standardize operator configuration source to `C:\Users\<current_user>\.obragconfig\.env` for easier post-boot management.
- Document restart procedure for Windows scheduled background task so config changes are reliably applied.
- Refine PDF pipeline to true OpenAI-first multimodal extraction with local OpenAI-compatible fallback only on OpenAI failure.
- Add PDF raw-file copy into vault `z.rawdata` and enforce backlink from generated markdown to copied raw file.
- Move PDF page images to temp-only lifecycle (ephemeral artifacts with cleanup), not persistent vault content.
- Add grayscale + readability-preserving image compression defaults for lower token usage on handwritten-note PDFs.
- Consolidate and harden all PDF prompts in `system_prompts.py` (no inline prompt strings in pipeline code).

## Capabilities

### New Capabilities
- `background-knowledge-generation`: Watch configured audio/PDF folders, normalize inputs into vault markdown, and index resulting content.
- `foreground-knowledge-generation`: Provide an MCP tool that actively updates a user-referenced markdown note (fuzzy resolution, summary/tags enrichment, path relocation) and reindexes affected vectors.
- `mcp-context-retrieval`: Provide an MCP tool that returns top-`k` semantically relevant chunks with source metadata from the vector database.

### Modified Capabilities
- None.

## Impact

- Affected code: new Python packages/modules for watchers, ingestion pipelines, model orchestration, chunking/embedding, vector storage adapter, MCP server/tool handlers, and config management.
- Affected code: path sanitization/validation layer for markdown output placement.
- APIs: MCP tool contracts for retrieval and active note update flows; OpenAI API calls for transcription/generation/embeddings; optional local OpenAI-compatible endpoint usage.
- Dependencies/systems: OpenAI Python SDK, optional transformer-based local ASR runtime, optional local OpenAI-compatible LLM runtime, PDF/OCR processing library, vector DB (e.g., Chroma/FAISS/Qdrant), Windows Task Scheduler or Startup integration, structured logging/metrics.
- Operational impact: API rate/latency handling for OpenAI calls; optional CPU/RAM spikes only when local ASR fallback is enabled; requires queueing, backpressure, and retry handling.
- Operational impact: background process reads config at startup only; operators must restart scheduled task after modifying `.obragconfig\.env`.
- Operational impact: temporary image lifecycle and cleanup become mandatory for PDF jobs; raw PDF storage increases vault usage in `z.rawdata`.
