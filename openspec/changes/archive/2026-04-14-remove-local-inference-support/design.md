## Context

The current codebase already routes most generation calls through an OpenAI-compatible API, but it still carries local-runtime scaffolding in several places. `background_worker/llm_runtime.py` includes local model load/eject logic plus a transformer-based ASR runtime, `config.py` still exposes flags and model settings intended for local execution, and packaging metadata still installs `transformers` and `torch`. Some call sites also retain `allow_local_fallback` style plumbing even though the supported operating model is now API-only.

This change is cross-cutting because runtime selection, worker behavior, configuration, dependency metadata, and operator docs all need to converge on one supported model: external API services only.

## Goals / Non-Goals

**Goals:**
- Remove all supported local inference paths for transcription, embeddings, and LLM generation.
- Simplify runtime code so worker and MCP flows assume API-backed services only.
- Remove local-only config fields and dependency declarations from shipped metadata.
- Update docs to describe one supported deployment model without local fallback language.

**Non-Goals:**
- Changing the external MCP contract or retrieval behavior.
- Introducing new providers or changing the API protocol from the current OpenAI-compatible approach.
- Reworking non-model-related ingestion logic.

## Decisions

1. Replace dual-mode runtime helpers with API-only service clients.
- Rationale: the code already uses remote clients for generation and embeddings, so keeping a second execution path adds dead weight and testing surface.
- Approach: remove `load_local_model`, `eject_local_model`, local ASR loading, and related fallback state from runtime helpers; keep only health checks or thin API-oriented helpers if they remain useful.
- Alternative considered: keep the code but mark it unsupported. Rejected because unsupported local code still shapes config, dependencies, and failure paths.

2. Remove local-only configuration keys and defaults.
- Rationale: fields such as `transcribe_local`, `generation_quant`, and local-model naming imply supported behaviors that will no longer exist.
- Approach: keep only endpoint and remote model identifiers needed by the API clients, and update env/docs accordingly.
- Alternative considered: deprecate keys but continue accepting them silently. Rejected because it prolongs ambiguity for operators and tests.

3. Remove heavyweight local-runtime dependencies from package metadata.
- Rationale: `transformers` and `torch` are no longer runtime requirements once local ASR/model loading is removed.
- Approach: delete them from `pyproject.toml`, `requirements.txt`, and any docs that instruct users to install or manage them.
- Alternative considered: keep them as optional extras. Rejected because local inference is explicitly out of scope.

4. Treat any remaining local-fallback call arguments as API-only no-ops and then remove them where practical.
- Rationale: several call sites pass `allow_local_fallback=True` despite always using `generation_mode=\"openai\"`.
- Approach: simplify call sites and client signatures so tests and production code reflect the actual API-only contract.
- Alternative considered: leave the parameters in place for compatibility. Rejected because the change is intended to eliminate local-runtime references from the supported surface area.

## Risks / Trade-offs

- [Older local-model environment files stop working] -> Mitigation: document the breaking change and fail clearly when unsupported keys are present or ignored.
- [Tests rely on old local-fallback method signatures] -> Mitigation: update test doubles and integration fixtures alongside the runtime cleanup.
- [A hidden local-runtime code path remains in docs or scripts] -> Mitigation: search config, source, tests, and docs for local-runtime terminology as part of validation.
- [Removing lazy transformer imports exposes an unhandled transcription dependency gap] -> Mitigation: ensure audio transcription has a supported API path before deleting local ASR code.

## Migration Plan

1. Audit source, tests, docs, and dependency files for local inference references.
2. Remove local runtime classes, fallback branches, and unused config fields.
3. Simplify API clients and call sites to expose only the supported remote contract.
4. Remove local-runtime packages from dependency metadata.
5. Update tests and runbooks to reflect the API-only setup.
6. Rollback strategy: restore the removed code and dependency entries from version control if local inference must be reintroduced in a future change.

## Open Questions

- None. The supported direction is API-only across transcription, embeddings, and generation.
