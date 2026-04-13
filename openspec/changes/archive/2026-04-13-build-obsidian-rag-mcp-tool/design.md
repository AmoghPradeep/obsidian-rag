## Context

This change introduces a Python-based Retrieval-Augmented Generation (RAG) pipeline around an Obsidian vault with two ingestion paths and one retrieval path. The current state has no standardized ingestion/indexing lifecycle for audio/PDF sources, no delta indexing for vault markdown changes, and no MCP-native query interface over embedded knowledge. Constraints include Windows-first operation for background startup, OpenAI API connectivity for primary inference paths, and bounded local memory usage when optional local ASR is enabled. Initial model choices are: local ASR fallback `cohere-transcribe-03-2026`, local generation fallback `gemma4-26B-A4B` (`Q3_K_M` quantized), and embeddings target `Qwen3-Embedding-0.6B` (while current runtime may use OpenAI embedding model).

## Goals / Non-Goals

**Goals:**
- Provide a startup background service that watches audio/PDF folders and converts new files into normalized vault markdown.
- Ensure generated markdown is chunked, embedded, and upserted into a vector database with source metadata.
- Provide an MCP tool to reindex changed/new markdown deltas in the vault.
- Provide an MCP tool to query top-k relevant context chunks from vector DB.
- Enforce predictable model lifecycle (load on job start, eject on completion/failure) to control RAM use.

**Non-Goals:**
- Building cloud-hosted orchestration, multi-tenant auth, or remote managed vector services.
- Replacing Obsidian authoring workflows or providing a full UI.
- Achieving perfect OCR/transcription fidelity for every noisy or low-quality source.

## Decisions

1. Python modular architecture with three runtime modules: `background_worker`, `mcp_server`, and shared `rag_core`.
- Rationale: keeps long-running watchers separated from request/response MCP tool execution while sharing chunking, embedding, and vector logic.
- Alternative considered: single monolithic process handling watchers and MCP endpoints. Rejected due to tighter failure coupling and harder restart behavior.

2. Event-driven ingestion with durable job queue and idempotency keys.
- Rationale: file watchers can emit duplicate events; queue + idempotency (`source_path + mtime + size + checksum`) prevents duplicate indexing.
- Alternative considered: direct inline processing from watcher callbacks. Rejected because it risks missed events and blocked watcher threads.

3. OpenAI-first runtime policy with OpenAI-compatible fallback endpoint.
- Rationale: transcription and generation should default to OpenAI APIs for best availability and lower local orchestration complexity; optional local OpenAI-compatible endpoint remains available as a secondary path.
- Alternative considered: local-first generation/transcription with service-health probes. Rejected in favor of API-first reliability and simpler operational model.

4. Audio ingestion preprocessing + normalization contract with domain tag governance.
- Rationale: all ingestion flows emit frontmatter + normalized sections (`source`, `created_at`, `summary`, `content`, `tags`) so chunking and retrieval stay consistent while enabling reusable domain taxonomy.
- Additional detail: audio files are preprocessed/compressed before transcription; normalization flow expects structured JSON response mapped into vault markdown and tags.
- Alternative considered: source-specific chunkers without normalization. Rejected because retrieval quality and metadata semantics become inconsistent.

5. Vector-store abstraction with local-first default.
- Rationale: define `VectorStore` interface (`upsert_chunks`, `delete_by_doc`, `query`) with Chroma as default adapter; enables future switch to FAISS/Qdrant.
- Alternative considered: hard-coding one backend. Rejected to reduce lock-in and testing limitations.

6. Foreground active note-update MCP tool (client-invoked).
- Rationale: foreground workflow is user intent driven, not generic vault-wide delta processing; updating one referenced note is simpler and better aligned with assistant usage.
- Required behavior: resolve target note from fuzzy user reference, preserve original body content, add/refresh `Summary` and `Tags` sections, optionally relocate note to recommended vault path, and reindex affected vectors.
- Alternative considered: generic delta reindex as primary foreground workflow. Rejected for weaker UX and higher unnecessary processing.

7. PDF multimodal map-reduce conversion strategy.
- Rationale: convert PDF pages to images (`pdf -> jpg`), run page-level multimodal extraction/summarization, and combine with map-reduce to improve handwritten-content capture and long-document summarization.
- Alternative considered: single-pass OCR-only extraction. Rejected due to weaker handwritten capture and lower summary quality on mixed-layout documents.

8. MCP API shape for retrieval and note-update workflows.
- Rationale: expose `query_vault_context` and `update_markdown_note` with strict input schema; outputs include retrieval chunks or note-update status/paths plus reindex effects.
- Alternative considered: single overloaded MCP tool. Rejected for poorer ergonomics and weaker observability.

9. Fuzzy + LLM-guided note resolution strategy.
- Rationale: client references may not exactly match file names; combining lexical shortlist with LLM-guided selection improves target accuracy.
- Required behavior: if confidence is low or ambiguous, tool returns candidate notes instead of mutating files.
- Alternative considered: strict exact-path updates only. Rejected for poor conversational usability.

10. Configurable chunking with practical defaults.
- Rationale: keep chunk parameters runtime-configurable and start with recommended defaults (`chunk_size=800`, `chunk_overlap=120`, token-based) to balance retrieval precision and context continuity.
- Alternative considered: fixed chunking constants. Rejected because different vault note styles need tuning.

11. Tag catalog reuse with controlled novelty.
- Rationale: maintain a tag catalog in storage; generation prompts bias toward existing domain tags and allow a new tag only when no existing tag fits.
- Alternative considered: unconstrained per-document tag generation. Rejected due to taxonomy drift and inconsistent retrieval grouping.

12. Optional local ASR fallback policy.
- Rationale: keep a `transcribe_local` switch for offline or cost-controlled runs using transformer ASR with explicit load/eject behavior.
- Alternative considered: API-only transcription with no local path. Rejected to preserve offline/emergency fallback.

13. Vault-relative path guardrails for LLM-generated markdown placement.
- Rationale: LLM may return absolute or malformed paths (for example `C--Users...`) when asked for `relativePath`; a deterministic sanitizer must enforce vault-relative output only.
- Required behavior: normalize separators, reject drive letters/UNC prefixes/rooted paths, collapse `.` and `..`, and resolve final path under vault root before write.
- Alternative considered: trusting LLM path directly. Rejected due to malformed folder creation risk and potential path traversal issues.

14. Prompt-level path constraints as first-line guardrail.
- Rationale: hardening the system prompt reduces invalid `relativePath` outputs and lowers correction/fallback frequency.
- Required behavior: prompt explicitly forbids absolute paths, drive letters, UNC paths, and traversal; prompt asks for repo/vault-relative path only.
- Trade-off: prompt-only controls are not sufficient by themselves; they must remain paired with sanitizer + containment checks.

15. Operator-facing config file in user home with explicit restart semantics.
- Rationale: background process starts at Windows boot and needs a stable, user-editable location for model/runtime variables.
- Required behavior: default `.env` path is `C:\Users\<current_user>\.obragconfig\.env`; nested settings use `__` delimiter.
- Required behavior: config is loaded once at startup; applying changes requires task restart (`schtasks /End` then `schtasks /Run`).
- Alternative considered: project-local `.env` only. Rejected because it is less discoverable/manageable for non-dev operators.

16. PDF pipeline provider routing: OpenAI-first, local OpenAI-compatible fallback.
- Rationale: keep PDF path simple (LLM + embeddings only; no ASR model in this flow) while ensuring resilience.
- Required behavior: call OpenAI first for page extraction/reduction; fallback to local OpenAI-compatible endpoint only when OpenAI call fails.
- Alternative considered: local-first routing for PDFs. Rejected due to higher operational complexity and inconsistent availability.

17. True multimodal PDF page extraction contract.
- Rationale: current workflow must transmit rendered page images to model input, not text-only placeholders.
- Required behavior: client must send image content for each page extraction call with strict schema-aligned response format.
- Alternative considered: OCR/text-only page processing. Rejected for weaker handwritten-note extraction quality.

18. Readability-preserving image optimization strategy.
- Rationale: token efficiency is needed, but handwritten small text must remain legible.
- Required behavior: grayscale conversion plus moderate compression (non-aggressive quality settings); no page classifier stage in current scope.
- Alternative considered: aggressive compression/downscale and classifier-based page skipping. Rejected as out-of-scope and quality-risky.

19. Raw PDF preservation and backlink integrity.
- Rationale: generated notes need traceability to original artifact inside vault.
- Required behavior: copy source PDF to `z.rawdata/pdf/` in vault and include backlink to copied file in generated markdown.
- Alternative considered: backlink to external watched-folder path. Rejected due to portability and broken-link risk.

20. Temp-only image artifact lifecycle for PDF jobs.
- Rationale: intermediate rendered images are transient processing artifacts and should not pollute vault.
- Required behavior: write page images to temp location and delete on success/failure in `finally` cleanup.
- Alternative considered: storing rendered images under vault folders. Rejected due to clutter and unintended indexing risk.

21. Prompt consolidation/hardening for PDF flow.
- Rationale: avoid drift from inline prompt strings and enforce stable output contracts.
- Required behavior: all PDF prompts (page extract, reduce, tags, markdown/backlink/path constraints) are defined in `system_prompts.py`.
- Alternative considered: ad-hoc inline prompts in pipeline modules. Rejected due to maintainability and regression risk.

## Risks / Trade-offs

- [OpenAI API latency/rate-limit instability] -> Mitigation: retry policy, queue backpressure, and bounded job concurrency.
- [High CPU/RAM spikes during local fallback model load] -> Mitigation: enable local ASR only when needed; single-flight job execution per model type.
- [File watcher race conditions/partial file writes] -> Mitigation: stable-file check (size/mtime unchanged across interval) before enqueue.
- [OCR/LLM normalization quality variance on handwritten PDFs] -> Mitigation: page-image multimodal extraction with map-reduce summary, store raw extraction alongside normalized markdown, annotate confidence flags.
- [Vector drift after foreground note updates/moves] -> Mitigation: update tool reindexes target note and removes stale vectors for old path when moved.
- [Wrong note chosen by fuzzy reference] -> Mitigation: confidence threshold + ambiguity response requiring user/client confirmation.
- [Update tool accidentally overwrites user content] -> Mitigation: preserve original body and append/refresh managed sections only.
- [Path relocation breaks links] -> Mitigation: safe move with containment checks and return old/new paths for caller reconciliation.
- [Long-running process reliability on Windows startup] -> Mitigation: Task Scheduler wrapper, heartbeat logging, retry policy, and crash-safe manifest persistence.
- [Config drift from stale long-running process] -> Mitigation: runbook restart procedure and explicit startup-only config loading contract.
- [Tag explosion and inconsistent domain labels] -> Mitigation: tag catalog reuse policy, similarity checks against existing tags, and explicit threshold for new-tag creation.
- [Malformed or absolute LLM file paths create bad vault folders] -> Mitigation: strict path sanitizer + vault-root containment check + fallback safe location when invalid.
- [Prompt regressions reintroduce invalid path output] -> Mitigation: regression tests over system prompt + parser contract plus runtime sanitizer as final guard.
- [PDF extraction silently degrades to text-only calls] -> Mitigation: multimodal payload tests and strict client contract verification.
- [Compression harms handwritten legibility] -> Mitigation: grayscale + moderate-quality defaults with integration checks on small-text pages.
- [Temp image leakage accumulates disk usage] -> Mitigation: guaranteed cleanup on both success and exception paths.

## Migration Plan

1. Introduce config file/env contract for vault paths, watched folders, model identifiers, chunk defaults, and vector backend.
2. Implement core pipeline modules and local integration tests.
3. Deploy background worker as startup task on Windows test machine.
4. Backfill existing vault markdown via one-time reindex command.
5. Enable MCP server tools for client integration and validate retrieval quality.
6. Rollback strategy: disable startup task and MCP tools, retain generated markdown; vector DB can be rebuilt from markdown manifest.

## Open Questions

- None for v1 scope; model/runtime and retrieval constraints are now fixed by current decisions.
