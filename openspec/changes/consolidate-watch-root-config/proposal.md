## Why

The current configuration model exposes four separate watch-path settings for audio, PDFs, image folders, and text files even though they are conceptually one incoming source tree. Consolidating them into a single configurable incoming root simplifies setup, reduces config drift, and makes the filesystem layout easier to reason about.

## What Changes

- **BREAKING** Replace `OBRAG_AUDIO_WATCH_PATH`, `OBRAG_PDF_WATCH_PATH`, `OBRAG_IMAGE_WATCH_PATH`, and `OBRAG_TEXT_WATCH_PATH` with one root setting.
- Add a single `incoming_root` configuration value and derive source directories as `<incoming_root>/audio`, `<incoming_root>/pdf`, `<incoming_root>/image`, and `<incoming_root>/text`.
- Keep the rest of the ingestion worker behavior unchanged by deriving the per-type watch paths from the shared root.
- Update tests and documentation to reflect the new config contract and directory layout.

## Capabilities

### New Capabilities
- `incoming-watch-root-config`: Define a single configurable incoming root that fans out into the fixed source subdirectories used by the background ingestion worker.

### Modified Capabilities

## Impact

- Affected code: `config.py`, background worker startup, tests that build `AppConfig`, and user-facing setup docs.
- API impact: no MCP behavior change.
- Operational impact: setup becomes simpler, but existing deployments must migrate from four watch-path env vars to one incoming-root env var.
