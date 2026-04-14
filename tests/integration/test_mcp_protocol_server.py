from pathlib import Path

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.mcp_server.server import MCPRuntime
from obsidian_rag_mcp.mcp_server.tools import MCPTools


class _FakeTools:
    def __init__(self) -> None:
        self.query_calls: list[tuple[str, int]] = []

    def query_vault_context(self, query: str, k: int) -> dict:
        self.query_calls.append((query, k))
        return {
            "k": 1,
            "results": [
                {
                    "chunk_id": "c1",
                    "content": "hello",
                    "doc_path": "vault/note.md",
                    "score": 0.92,
                    "source": {"doc_path": "vault/note.md", "chunk_id": "c1"},
                    "similarity_score": 0.92,
                }
            ],
        }

    def update_markdown_note(self, note_reference: str, update_context: str = "", confidence_threshold: float = 0.65) -> dict:
        return {
            "status": "updated",
            "note_reference": note_reference,
            "confidence": 0.91,
            "confidence_threshold": confidence_threshold,
            "resolved_file": "vault/note.md",
            "old_path": "vault/note.md",
            "new_path": "vault/note.md",
            "moved": False,
            "path_fallback_used": False,
            "summary_updated": True,
            "tags_updated": True,
            "changes_applied": True,
            "indexed_chunks": 2,
            "candidate_count": 1,
        }


def test_mcp_tool_discovery_and_query_invocation() -> None:
    runtime = MCPRuntime(_FakeTools())

    init_resp = runtime.handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init_resp is not None
    assert init_resp["result"]["capabilities"]["tools"]["listChanged"] is False

    list_resp = runtime.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert list_resp is not None
    tools = list_resp["result"]["tools"]
    names = [t["name"] for t in tools]
    assert names == ["query_vault_context", "update_markdown_note"]
    query_schema = next(t["inputSchema"] for t in tools if t["name"] == "query_vault_context")
    assert "query" in query_schema["properties"]

    call_resp = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "query_vault_context", "arguments": {"query": "hello", "k": 3}},
        }
    )
    assert call_resp is not None
    payload = call_resp["result"]["structuredContent"]
    assert payload["k"] == 1
    assert payload["results"][0]["similarity_score"] == 0.92


def test_mcp_validation_and_runtime_error_contracts() -> None:
    runtime = MCPRuntime(_FakeTools())

    validation = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "query_vault_context", "arguments": {"k": 5}},
        }
    )
    assert validation is not None
    assert validation["error"]["code"] == -32602
    assert validation["error"]["message"] == "Invalid tool arguments"

    class _ExplodingTools(_FakeTools):
        def query_vault_context(self, query: str, k: int) -> dict:
            raise RuntimeError("boom")

    runtime = MCPRuntime(_ExplodingTools())
    runtime_error = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "query_vault_context", "arguments": {"query": "x", "k": 1}},
        }
    )
    assert runtime_error is not None
    assert runtime_error["error"]["code"] == -32000
    assert runtime_error["error"]["message"] == "Tool execution failed"
    assert runtime_error["error"]["data"]["tool"] == "query_vault_context"


def test_mcp_update_markdown_note_success_and_ambiguity(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    audio = tmp_path / "audio"
    pdf = tmp_path / "pdf"
    images = tmp_path / "images"
    for p in (vault, audio, pdf, images):
        p.mkdir(parents=True, exist_ok=True)

    target = vault / "scratch" / "My Note.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# My Note\n\nOriginal body content.", encoding="utf-8")

    cfg = AppConfig(
        vault_path=vault,
        audio_watch_path=audio,
        pdf_watch_path=pdf,
        image_watch_path=images,
        db_path=tmp_path / "db.sqlite3",
        queue_path=tmp_path / "jobs.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )
    tools = MCPTools(cfg)
    runtime = MCPRuntime(tools)

    def fake_chat_success(prompt: str, images=None, generation_mode="openai", allow_local_fallback=True, require_success=False):
        if "Pick the best markdown file" in prompt:
            escaped = str(target).replace("\\", "\\\\")
            return f'{{"selected_path":"{escaped}","confidence":0.95}}'
        if "Summarize this markdown note" in prompt:
            return "- concise summary"
        if "Return up to 8 broad knowledge-domain tags" in prompt:
            return "learning,notes"
        if "Select the best vault-relative directory" in prompt:
            return "knowledge/notes"
        return ""

    monkeypatch.setattr(tools.llm_client, "chat", fake_chat_success)
    success = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {
                "name": "update_markdown_note",
                "arguments": {"note_reference": "my note", "update_context": "organize it", "confidence_threshold": 0.65},
            },
        }
    )
    assert success is not None
    success_payload = success["result"]["structuredContent"]
    assert success_payload["status"] == "updated"
    assert success_payload["changes_applied"] is True
    assert Path(success_payload["new_path"]).exists()

    sibling = vault / "knowledge" / "notes" / "My Note Copy.md"
    sibling.parent.mkdir(parents=True, exist_ok=True)
    sibling.write_text("# Copy", encoding="utf-8")

    monkeypatch.setattr(tools.llm_client, "chat", lambda *_args, **_kwargs: '{"selected_path":"","confidence":0.2}')
    ambiguous = runtime.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 22,
            "method": "tools/call",
            "params": {
                "name": "update_markdown_note",
                "arguments": {"note_reference": "note", "update_context": "", "confidence_threshold": 0.8},
            },
        }
    )
    assert ambiguous is not None
    ambiguous_payload = ambiguous["result"]["structuredContent"]
    assert ambiguous_payload["status"] == "ambiguous"
    assert ambiguous_payload["changes_applied"] is False
