## 1. Runtime Cleanup

- [x] 1.1 Audit the codebase for local inference references across worker, MCP, client, config, docs, and tests
- [x] 1.2 Remove local LLM and ASR runtime management from `background_worker/llm_runtime.py` and related worker flows
- [x] 1.3 Remove local fallback arguments and dead branching from API client call sites and test doubles

## 2. Configuration and Dependencies

- [x] 2.1 Remove local-only model settings and flags from `config.py` and the `OBRAG_` configuration surface
- [x] 2.2 Remove local inference packages from `pyproject.toml` and `requirements.txt`
- [x] 2.3 Update startup validation and defaults so only API-backed model configuration remains

## 3. Documentation and Validation

- [x] 3.1 Remove local inference references from runbooks, README content, and operator guidance
- [x] 3.2 Update unit and integration tests to reflect the API-only runtime contract
- [x] 3.3 Run the relevant test suite and verify no local inference references remain in supported code paths
