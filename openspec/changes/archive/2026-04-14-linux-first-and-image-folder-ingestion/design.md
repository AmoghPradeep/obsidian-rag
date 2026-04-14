## Context

The current repository is operationally centered on Windows: default config examples use Windows paths, startup automation relies on Task Scheduler, and the runbook assumes a Windows host. The ingestion side currently supports audio files and PDFs, where PDFs are rendered into page images and then processed through a multimodal LLM flow that produces one normalized markdown note in the Obsidian vault.

The new requirement has two parts. First, Linux must become the primary deployment target. Second, the system must ingest exported note folders that contain multiple page images, such as `note-1/image-1-of-3.png`, `note-1/image-2-of-3.png`, and `note-1/image-3-of-3.png`, and combine them into one markdown note. The existing PDF pipeline already performs page-by-page multimodal extraction and downstream markdown normalization, so the new image-folder flow should reuse that logic rather than duplicating it.

## Goals / Non-Goals

**Goals:**
- Make configuration defaults, runbooks, and service management Linux-first.
- Preserve cross-platform behavior where practical without keeping Windows as the primary operating model.
- Add a watched image-folder ingestion path where one directory maps to one logical note.
- Reuse the PDF page extraction and markdown generation flow for image folders.
- Define deterministic folder ordering, completion detection, and idempotency rules for multi-image documents.

**Non-Goals:**
- Adding new MCP tools or changing the retrieval contract.
- Replacing the current audio or PDF business workflows beyond shared refactoring.
- Building a distributed worker system or remote orchestration layer.

## Decisions

1. Platform defaults become Linux-first, with conditional Windows compatibility.
- Rationale: the deployment target has changed, so defaults and operator guidance must match the primary environment.
- Required behavior: config examples, default path conventions, and service setup instructions target Linux first; Windows remains a secondary compatibility path.
- Alternative considered: keep Windows defaults and add Linux as optional documentation. Rejected because it preserves the wrong operational center of gravity.

2. Introduce a dedicated watched image-document root where each immediate child directory is one document.
- Rationale: Apple Notes style exports are naturally folder-scoped and should be processed as one unit.
- Required behavior: the watcher treats a directory such as `/watched/note-1/` as one job, not three separate image jobs.
- Alternative considered: watch loose image files individually. Rejected because it loses document grouping and produces fragmented notes.

3. Refactor PDF page processing into a shared page-document pipeline.
- Rationale: both PDFs and image folders are sequences of page images followed by the same multimodal transcription, reduction, tagging, and markdown write steps.
- Required behavior: PDF ingestion becomes `pdf -> rendered images -> shared page-document pipeline`; image-folder ingestion becomes `folder images -> shared page-document pipeline`.
- Alternative considered: clone the PDF logic into a second pipeline. Rejected because it would create prompt drift and duplicate bug-fix work.

4. Use deterministic image ordering with natural numeric filename sorting.
- Rationale: exported note pages often use filenames like `image-1-of-3.png`; lexical sort alone can misorder pages.
- Required behavior: files are ordered by a natural sort over filename segments, with a documented fallback to path order if numbering is absent.
- Alternative considered: rely on filesystem enumeration or modification time. Rejected because those are unstable across copies and hosts.

5. Folder ingestion uses stable-directory detection and directory-level idempotency.
- Rationale: copied exports may arrive incrementally, and processing must not start before all images are present.
- Required behavior: a folder is eligible only after its contents remain unchanged across a stability window; idempotency is based on the folder path plus member file fingerprints.
- Alternative considered: enqueue on first observed file. Rejected because partial folders would produce incomplete notes.

6. Linux service management uses systemd in the runbook and packaging guidance.
- Rationale: Linux-first operation needs a supported service model analogous to the current Windows scheduled startup.
- Required behavior: docs and scripts describe a systemd unit and restart workflow; Windows Task Scheduler guidance may remain as a secondary appendix or compatibility note.
- Alternative considered: keep only manual CLI instructions. Rejected because the project is explicitly intended as a long-running background service.

## Risks / Trade-offs

- [Linux path and env default changes break existing Windows setups] -> Mitigation: use platform-aware defaults and document Windows overrides explicitly.
- [Folder stability detection delays ingestion for large exports] -> Mitigation: keep the stability window configurable and log why folders are deferred.
- [Shared refactor introduces regressions in the existing PDF flow] -> Mitigation: add regression tests that exercise PDF ingestion through the shared page-document path.
- [Natural sorting still fails for irregular export names] -> Mitigation: document the fallback behavior and return explicit job errors for empty or invalid folders.
- [Directory-level idempotency misses changes when one page is replaced] -> Mitigation: compute folder fingerprints from all member files, not only the directory timestamp.

## Migration Plan

1. Introduce Linux-oriented configuration defaults and add platform-aware path resolution.
2. Extract the PDF image-sequence logic into a shared page-document pipeline.
3. Add a new watched image-folder root and directory-stability detection.
4. Route folder image jobs through the shared page-document pipeline and index the resulting markdown.
5. Update runbooks and startup guidance for systemd-first Linux operation.
6. Rollback strategy: disable the new image-folder watcher and revert to the previous platform-specific operational guidance; existing vault content and vector data remain rebuildable from markdown sources.

## Open Questions

- None for proposal scope; Linux-first operations and folder-scoped multi-image ingestion are the selected direction.
