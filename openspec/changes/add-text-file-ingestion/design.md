## Context

The current background worker processes three source types: audio files, PDFs, and folders of page images. Audio already follows a lightweight prompt-to-JSON normalization flow after transcription, while PDFs and image folders use a heavier multimodal page-extraction pipeline before producing normalized markdown. Text files are simpler than either path because they already contain plain text, but they still need the same downstream normalization, safe vault write behavior, tagging, and indexing.

The user explicitly wants this to stay close to the existing pipeline style rather than becoming a special-case file copier. That means the new flow should preserve the current prompt-driven normalization pattern and fit naturally into the watcher, queue, raw-source copy, and indexing model already in place.

## Goals / Non-Goals

**Goals:**
- Add a watched text-input source for `.txt` and `.md` files.
- Normalize source text into Obsidian markdown through the existing prompt-to-JSON style.
- Reuse existing markdown writing, tag persistence, raw-source preservation, and indexing behavior.
- Keep the implementation lightweight and aligned with the current worker architecture.

**Non-Goals:**
- Introducing a new MCP tool or changing retrieval behavior.
- Building a separate parsing framework for rich text, HTML, or office documents.
- Preserving imported `.md` files byte-for-byte without normalization.
- Redesigning the existing audio, PDF, or image-folder flows beyond small shared helpers if needed.

## Decisions

1. Add a distinct text watch path and queue job type.
- Rationale: the current worker model is source-type oriented, and a dedicated `text` job keeps routing, raw-data storage, and logging explicit.
- Alternative considered: treat text files as image-folder or PDF variants. Rejected because the worker dispatch and source preparation logic are already organized around separate job types.

2. Support `.txt` and `.md` as the initial accepted extensions.
- Rationale: these are the concrete formats requested and match the “simple subset” framing.
- Alternative considered: accepting every text-like extension such as `.rst`, `.csv`, or `.json`. Rejected because it broadens semantics and prompt expectations without a requirement.

3. Reuse the existing prompt-to-JSON markdown-normalization style used by the audio flow.
- Rationale: the source is already text, so it can skip transcription and go directly into the same style of normalization that maps freeform content into vault-relative markdown plus tags.
- Alternative considered: write imported text directly into the vault with minimal wrapping. Rejected because it would create format drift relative to the rest of the generated knowledge corpus.

4. Preserve raw source files in `z.rawdata/text/` and backlink them from generated notes when practical.
- Rationale: the other ingestion paths retain provenance, and text imports should remain inspectable after normalization.
- Alternative considered: normalize in place without keeping the source. Rejected because it weakens traceability and makes later audits harder.

5. Keep `.md` imports normalized rather than trusted as final vault notes.
- Rationale: external markdown may not follow the project’s path, tag, or note-shape conventions, so normalization keeps ingestion behavior consistent.
- Alternative considered: bypass the LLM for `.md` and copy directly. Rejected because the user explicitly asked to follow the existing prompt style.

## Risks / Trade-offs

- [Normalization may rewrite already-good markdown more than necessary] -> Mitigation: keep prompts conservative and frame the input as source material to organize rather than content to invent from.
- [Users may expect all markdown syntax to survive exactly] -> Mitigation: document that this is an ingestion-and-normalization pipeline, not a lossless importer.
- [A new watch path adds configuration overhead] -> Mitigation: follow the existing config naming pattern and update the runbook/examples in the same change.
- [Prompt reuse may fit `.txt` better than `.md`] -> Mitigation: test both extensions and adjust wording so the same prompt handles plain text and preformatted markdown safely.

## Migration Plan

1. Add text-watch configuration and watcher enqueue logic for stable `.txt` and `.md` files.
2. Implement a text pipeline that reads source content, runs prompt-to-JSON normalization, writes markdown to the vault, and persists tags.
3. Route text jobs through the background worker with raw-source copying and post-write indexing.
4. Add integration and watcher tests for `.txt` and `.md` ingestion.
5. Update README and runbook examples to include the new text-input source.

## Open Questions

None.
