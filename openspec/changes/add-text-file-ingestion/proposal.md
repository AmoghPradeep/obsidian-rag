## Why

The ingestion system already handles audio, PDFs, and image folders, but it still excludes simple text sources that are easier to import than transcribing or rendering documents. Adding `.txt` and `.md` ingestion now closes that gap with a low-complexity pipeline that reuses the same normalization style already proven in the existing workflows.

## What Changes

- Add a new background ingestion pipeline for text-based files: `.txt` and `.md`.
- Add a watched text-input directory and enqueue stable text file jobs alongside the existing audio, PDF, and image-folder jobs.
- Normalize imported text files into Obsidian markdown using the same prompt-to-JSON markdown-generation style already used in the current pipelines.
- Write the normalized markdown note into the vault, persist tags, and index the result for retrieval.
- Preserve raw source copies under the vault raw-data area so generated notes retain source provenance.

## Capabilities

### New Capabilities
- `text-file-knowledge-generation`: Import `.txt` and `.md` files through the background worker, normalize them into vault markdown, and index the resulting knowledge for retrieval.

### Modified Capabilities

## Impact

- Affected code: config loading, watcher/queue logic, background worker dispatch, prompt helpers or prompt reuse, a new text pipeline module, tests, and runbook/README documentation.
- API impact: no MCP surface change is required.
- Operational impact: users gain a fourth ingestion source type with a simple file-drop workflow for existing text notes and exports.
