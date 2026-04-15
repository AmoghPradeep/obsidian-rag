## 1. Watcher And Config

- [x] 1.1 Add a configured text watch path and extend watcher scanning to enqueue stable `.txt` and `.md` files as `text` jobs.
- [x] 1.2 Extend source preparation and worker dispatch so text jobs preserve raw source copies and route into a dedicated text pipeline.

## 2. Text Pipeline

- [x] 2.1 Implement a text-ingestion pipeline that reads source content and normalizes it into vault markdown using the existing prompt-to-JSON style.
- [x] 2.2 Preserve provenance and tag persistence for generated text notes without changing existing retrieval/indexing behavior.

## 3. Verification And Docs

- [x] 3.1 Add watcher and end-to-end integration tests for `.txt` and `.md` ingestion.
- [x] 3.2 Update README and runbook documentation to describe the new text-input pipeline and configuration.
