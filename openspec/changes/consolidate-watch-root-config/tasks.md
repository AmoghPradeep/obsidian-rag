## 1. Config Model

- [x] 1.1 Replace separate watch-path settings with one `incoming_root` config value and derive per-type source directories from it.
- [x] 1.2 Update startup directory creation and worker logging to use the derived child directories under the shared root.

## 2. Verification

- [x] 2.1 Update tests that construct `AppConfig` so they use the shared incoming root and the new `image` subdirectory name.
- [x] 2.2 Run the full test suite and confirm the routing behavior remains unchanged.

## 3. Documentation

- [x] 3.1 Update README and runbook configuration examples to describe `TOTAL_RECALL_INCOMING_ROOT` and the derived `/audio`, `/pdf`, `/image`, and `/text` directories.
