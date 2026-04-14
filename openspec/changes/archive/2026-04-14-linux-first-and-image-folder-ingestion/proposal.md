## Why

The repository was built around Windows-specific assumptions, but the primary deployment target is now Linux. At the same time, the ingestion system handles PDFs and audio, but not a common real-world source: note exports represented as folders of ordered images, such as Apple Notes exports.

## What Changes

- Shift runtime, configuration, paths, startup guidance, and operational scripts to a Linux-first model while keeping Windows compatibility only where practical.
- Add background ingestion for watched image-document folders where each folder contains multiple page images belonging to a single note.
- Reuse the existing PDF multimodal extraction and markdown-normalization flow for image folders so page transcription, summary generation, tagging, and vault writes stay consistent across document types.
- Define ordering, grouping, and completion rules for multi-image folders so all images in one folder are combined into a single Obsidian markdown note.
- Update runbooks, tests, and startup/deployment guidance to cover Linux-first setup and the new image-folder ingestion path.
- **BREAKING**: default operator workflow, environment examples, and startup instructions will target Linux instead of Windows.

## Capabilities

### New Capabilities
- `linux-runtime-and-ops`: Run, configure, and operate the system primarily on Linux hosts.
- `image-folder-knowledge-generation`: Watch folders of related page images, transcribe them as one document, normalize the result, and write one markdown note into the vault.

### Modified Capabilities
- None.

## Impact

- Affected code: configuration loading, path handling, startup scripts, background watchers, image/PDF pipeline sharing, and runbook documentation.
- Affected systems: Linux service management and filesystem layout become the default operating model.
- APIs: no new MCP tools are required, but ingested content available to retrieval and note-update flows will expand through the new image-folder source type.
