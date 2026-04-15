# Runbook

## Configuration

Configuration is loaded in this order:

1. Environment variables prefixed with `TOTAL_RECALL_`
2. `.env` file at `~/.total-recall/.env`
3. Code defaults

Nested config keys use `__` separators (for example `TOTAL_RECALL_MODELS__GENERATION_MODEL`).

- `TOTAL_RECALL_VAULT_PATH`
- `TOTAL_RECALL_INCOMING_ROOT`
- `TOTAL_RECALL_DB_PATH`
- `TOTAL_RECALL_MANIFEST_PATH`
- `TOTAL_RECALL_QUEUE_PATH`
- `TOTAL_RECALL_WATCHER_STABILITY_SECONDS`
- `TOTAL_RECALL_MODELS__API_BASE_URL` (default `https://api.openai.com/v1`)
- `TOTAL_RECALL_MODELS__GENERATION_MODEL`
- `TOTAL_RECALL_MODELS__TRANSCRIPTION_MODEL`
- `TOTAL_RECALL_MODELS__EMBEDDING_MODEL`
- `TOTAL_RECALL_CHUNKING__CHUNK_SIZE` (default `800`)
- `TOTAL_RECALL_CHUNKING__CHUNK_OVERLAP` (default `120`)

Create/update `~/.total-recall/.env`:

```dotenv
TOTAL_RECALL_VAULT_PATH=/home/<current_user>/Documents/total-recall-vault
TOTAL_RECALL_INCOMING_ROOT=/home/<current_user>/.total-recall/incoming
TOTAL_RECALL_DB_PATH=/home/<current_user>/.total-recall/data/rag.sqlite3
TOTAL_RECALL_MODELS__API_BASE_URL=https://api.openai.com/v1
TOTAL_RECALL_MODELS__GENERATION_MODEL=gpt-5.4-mini
TOTAL_RECALL_MODELS__TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
TOTAL_RECALL_MODELS__EMBEDDING_MODEL=text-embedding-3-large
```

The app derives its watched source folders from `TOTAL_RECALL_INCOMING_ROOT`:

- `audio`
- `pdf`
- `image`
- `text`

Each immediate child directory under `TOTAL_RECALL_INCOMING_ROOT/image` is treated as one multi-image document. For example, `.../image/note-1/image-1-of-3.png` and `image-2-of-3.png` are combined into one markdown note.
Files placed under `TOTAL_RECALL_INCOMING_ROOT/text` are ingested as text sources when they have `.txt` or `.md` extensions.

## Start background worker

```powershell
total-recall-background
```

## Start MCP tool server

```powershell
total-recall-server
```

MCP clients should use JSON-RPC over stdio with `initialize`, `tools/list`, and `tools/call`.
Example request flow (one JSON object per line):

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"query_vault_context","arguments":{"query":"what did we discuss about meeting notes?","k":5}}}
```

The server exposes one tool:
- `query_vault_context`

See `docs/mcp-migration.md` for migration details from the legacy custom JSON loop.

## Linux service setup

Copy `scripts/total-recall-background.service.example` to `~/.config/systemd/user/total-recall-background.service`, adjust `WorkingDirectory` if needed, then enable it:

```bash
mkdir -p ~/.config/systemd/user
cp scripts/total-recall-background.service.example ~/.config/systemd/user/total-recall-background.service
systemctl --user daemon-reload
systemctl --user enable --now total-recall-background.service
```

## Updating config for Linux service

1. Edit `~/.total-recall/.env`.
2. Restart the user service so it reloads variables.

```bash
systemctl --user restart total-recall-background.service
```

Note: config is read only at process startup. Changes do not apply until restart.

## Windows compatibility

Windows remains supported through explicit path overrides and the existing Task Scheduler script:

```powershell
.\scripts\register-startup-task.ps1
```

## Recovery

- Rebuild vectors: delete `manifest.json`, then restart the background worker so changed notes are re-indexed.
- If tags drift: clear `doc_tags` and `tags` tables in `rag.sqlite3` and re-run indexing.
- If API calls fail, verify the configured base URL, credentials, and model names, then restart the worker after fixing the configuration.
