## Why

The repository still carries code paths, configuration, and dependencies for local transcription, embedding, and text-generation models even though the intended operating model is now fully API-based. Keeping both modes increases runtime complexity, confuses operators, and pulls in heavyweight packages that are no longer part of the supported deployment.

## What Changes

- Remove local inference support for transcription, embeddings, and LLM generation from application code and worker flows.
- Remove configuration fields, defaults, and environment handling that exist only to support local model loading or local inference routing.
- Remove local inference dependencies from packaging metadata and requirements files.
- Update runbooks and related docs so the supported architecture is clearly API-only.
- **BREAKING**: deployments that relied on bundled local model execution or local fallback behavior must be reconfigured to use supported remote/API endpoints only.

## Capabilities

### New Capabilities
- `api-only-inference-runtime`: Run transcription, normalization, and retrieval workflows exclusively through configured API services without any local model runtime.

### Modified Capabilities
- None.

## Impact

- Affected code: background worker runtime selection, model configuration, startup validation, and dependency declarations.
- Affected systems: operator setup becomes simpler because local GPU/model runtime support is removed.
- Dependencies: local-runtime packages such as `transformers` and `torch` are removed from the supported install set.
