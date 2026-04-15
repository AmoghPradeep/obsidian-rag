## Context

The background worker currently treats audio, PDF, image-folder, and text ingestion as separate source types, and that part of the design remains sound. The awkward part is configuration: users must supply or accept four separate watch paths even though all four directories live under the same logical incoming area. This adds unnecessary configuration surface and makes docs and tests more repetitive.

The desired outcome is not to collapse the pipelines themselves, but to collapse the watch-path configuration model. The worker should still route by source type, but the path fan-out should come from one base directory plus fixed subdirectory names.

## Goals / Non-Goals

**Goals:**
- Replace the four watch-path settings with one configurable incoming root.
- Derive the runtime source directories as `<incoming_root>/audio`, `/pdf`, `/image`, and `/text`.
- Minimize churn in the rest of the codebase by preserving the current worker-facing per-type path access pattern where useful.
- Update tests and docs to make the new config contract explicit.

**Non-Goals:**
- Changing ingestion semantics for any pipeline.
- Combining the four pipelines into one processor.
- Making the subdirectory names configurable independently.

## Decisions

1. Add one `incoming_root` config field and derive per-type watch paths as computed properties.
- Rationale: this removes redundant configuration without forcing invasive changes through the worker and watcher code.
- Alternative considered: pass `incoming_root` everywhere and derive child paths ad hoc. Rejected because computed properties keep call sites stable and isolate the change to config.

2. Use fixed subdirectory names: `audio`, `pdf`, `image`, and `text`.
- Rationale: the user explicitly asked for this pattern, and fixed names keep the contract simple.
- Alternative considered: preserve `images` as the folder name for compatibility. Rejected because the requested layout is singular `image`.

3. Remove the separate watch-path env vars from the supported config contract.
- Rationale: the goal is simplification; retaining both old and new settings would preserve ambiguity and precedence complexity.
- Alternative considered: temporary dual support with deprecation. Rejected because the requested direction is to stop having four independent path configs.

## Risks / Trade-offs

- [Existing deployments still set the old watch-path env vars] -> Mitigation: update docs clearly and treat the change as breaking.
- [Tests or scripts assume the old `incoming/images` path] -> Mitigation: update all config-constructing tests and run the full suite.
- [Changing the image subdirectory name from `images` to `image` surprises operators] -> Mitigation: document the new layout directly in the runbook and README.

## Migration Plan

1. Replace watch-path config fields with one `incoming_root` field in the settings model.
2. Derive per-type watch paths from `incoming_root` and create the child directories at startup.
3. Update tests to create the new `audio`, `pdf`, `image`, and `text` child directories beneath one incoming root.
4. Update README and runbook examples to use `TOTAL_RECALL_INCOMING_ROOT`.

## Open Questions

None.
