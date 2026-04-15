# Repository Guidelines

## Project Structure & Module Organization
`src/total_recall/` contains the application code. Keep RAG logic under `rag_core/`, MCP stdio server code under `mcp_server/`, and long-running ingestion logic under `background_worker/`. Tests live in `tests/unit/` and `tests/integration/`. Operational docs are in `docs/`, service/bootstrap helpers in `scripts/`, and design history in `openspec/changes/archive/`.

## Build, Test, and Development Commands
Use Python 3.11+.

```powershell
python -m pip install -e .[test]
pytest
pytest tests/unit
pytest tests/integration
total-recall-background
total-recall-server
```

`python -m pip install -e .[test]` installs the package plus pytest. `pytest` runs the full suite. Use the unit or integration path filters for faster iteration. `total-recall-background` starts the vault watcher and ingestion worker; `total-recall-server` starts the JSON-RPC MCP server over stdio.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, type hints on public functions, and small focused modules. Use `snake_case` for files, functions, and variables; `PascalCase` for Pydantic models and service classes; `UPPER_CASE` for constants such as `DEFAULT_ENV_FILE`. Prefer explicit imports from `total_recall.*` and keep platform-aware config/path logic centralized in `config.py` or dedicated utilities.

## Testing Guidelines
Pytest is the test framework. Name files `test_*.py` and keep test functions behavior-focused, for example `test_chunking_overlap_and_ids`. Put isolated logic checks in `tests/unit/`; use `tests/integration/` for end-to-end flows such as MCP calls, PDF/audio pipelines, and path-safety behavior. Add or update tests with every behavior change.

## Commit & Pull Request Guidelines
Recent commits use short, plain-language subjects like `more tests`, `bugfixes`, and `fixes + refinements`. Keep commits narrowly scoped and write brief present-tense summaries. For pull requests, include:

- What changed and why
- Test evidence (`pytest`, targeted test path, or manual MCP flow)
- Config or runbook updates if behavior or env vars changed
- Linked OpenSpec change or issue when applicable

## Security & Configuration Tips
Configuration loads from `TOTAL_RECALL_` environment variables, then `~/.total-recall/.env`, then code defaults. Do not commit local vault paths, model endpoints, or generated SQLite/manifest data. If you change startup or operational behavior, update `docs/runbook.md` in the same PR.
