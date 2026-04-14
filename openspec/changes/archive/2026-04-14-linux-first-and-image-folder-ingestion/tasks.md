## 1. Linux-First Runtime and Operations

- [x] 1.1 Update configuration defaults and path resolution to use Linux-first locations and platform-aware fallbacks
- [x] 1.2 Add a configurable image watch root to the application settings and environment contract
- [x] 1.3 Replace or complement Windows-first startup guidance with Linux service-management support and examples
- [x] 1.4 Update runbook and related docs to describe Linux-first deployment, restart, and config reload workflows

## 2. Shared Page-Document Pipeline

- [x] 2.1 Extract the PDF image-sequence transcription, reduction, tagging, and markdown-generation flow into a shared page-document pipeline
- [x] 2.2 Refactor the existing PDF pipeline to render pages and then call the shared page-document pipeline without changing its output contract
- [x] 2.3 Preserve existing vault write, backlink, tagging, and indexing behavior when the shared pipeline is used from PDF ingestion

## 3. Image-Folder Ingestion

- [x] 3.1 Implement image-folder discovery so each immediate child directory under the watched image root is treated as one source document
- [x] 3.2 Implement supported-image filtering and deterministic natural filename ordering for page images inside one directory
- [x] 3.3 Implement stable-directory detection so partially copied folders are deferred until contents stop changing
- [x] 3.4 Implement directory-level idempotency based on folder contents so unchanged exports are skipped and changed exports are reprocessed
- [x] 3.5 Route image-folder jobs through the shared page-document pipeline and write one markdown note per source directory

## 4. Background Worker Integration

- [x] 4.1 Extend watcher and queue logic to enqueue image-folder jobs alongside existing audio and PDF jobs
- [x] 4.2 Update job execution and metrics handling so image-folder jobs are processed and indexed correctly
- [x] 4.3 Add error handling and logging for empty folders, unsupported files, ordering failures, and partial-copy deferrals

## 5. Validation

- [x] 5.1 Add unit tests for Linux-aware config/path behavior and natural sorting of image filenames
- [x] 5.2 Add unit or integration tests for stable-directory detection and directory-level idempotency
- [x] 5.3 Add regression tests proving the PDF pipeline still works through the shared page-document implementation
- [x] 5.4 Add end-to-end integration tests for multi-image folder ingestion producing one vault markdown note and retrievable indexed content
