from __future__ import annotations

import logging
from pathlib import Path

from obsidian_rag_mcp.background_worker.audio_pipeline import process_audio_to_markdown
from obsidian_rag_mcp.background_worker.queue import DurableJobQueue, IngestionJob
from obsidian_rag_mcp.mcp_server.server import MCPRuntime
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.tags import TagCatalog
from obsidian_rag_mcp.rag_core.vector_store.sqlite_store import SQLiteVectorStore


def test_durable_queue_logs_enqueue_duplicate_and_pop(tmp_path: Path, caplog) -> None:
    queue = DurableJobQueue(tmp_path / "jobs.jsonl")
    job = IngestionJob(job_type="audio", source_path="voice.m4a", idempotency_key="abc")

    with caplog.at_level(logging.DEBUG):
        assert queue.enqueue(job) is True
        assert queue.enqueue(job) is False
        popped = queue.pop_all()

    assert len(popped) == 1
    assert "Enqueued job job_type=audio source=voice.m4a" in caplog.text
    assert "Skipping duplicate queue entry job_type=audio source=voice.m4a idempotency_key=abc" in caplog.text
    assert "Popped queued jobs count=1" in caplog.text


def test_audio_pipeline_logs_exception_with_source_context(tmp_path: Path, monkeypatch, caplog) -> None:
    vault = tmp_path / "vault"
    vault.mkdir(parents=True, exist_ok=True)
    audio = tmp_path / "note.m4a"
    audio.write_bytes(b"audio")

    monkeypatch.setattr("obsidian_rag_mcp.background_worker.audio_pipeline.compress_for_asr_tempdir", lambda path: path)

    class _FailingClient:
        def transcribe_audio(self, *_args, **_kwargs):
            raise RuntimeError("transcription boom")

        def chat(self, *_args, **_kwargs):
            return ""

    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    tag_catalog = TagCatalog(store)

    with caplog.at_level(logging.ERROR):
        result = process_audio_to_markdown(
            source_audio=audio,
            output_md=vault,
            llm_client=_FailingClient(),
            tag_catalog=tag_catalog,
            transcription_model="gpt-4o-mini-transcribe",
        )

    assert result.success is False
    assert f"Audio pipeline failed source={audio}" in caplog.text


def test_llm_client_failure_logs_do_not_include_prompt(monkeypatch, caplog) -> None:
    client = OpenAICompatibleClient("https://api.openai.com/v1", "gpt-5.4-mini")

    def fail():
        raise RuntimeError("network down")

    monkeypatch.setattr(client, "_client", fail)

    with caplog.at_level(logging.ERROR):
        result = client.chat("very secret prompt body", require_success=False)

    assert result == "very secret prompt body"[:2000]
    assert "Generation request failed" in caplog.text
    assert "very secret prompt body" not in caplog.text


def test_mcp_runtime_logs_tool_execution_failure(caplog) -> None:
    class _ExplodingTools:
        def query_vault_context(self, query: str, k: int) -> dict:
            raise RuntimeError("boom")

    runtime = MCPRuntime(_ExplodingTools())

    with caplog.at_level(logging.WARNING):
        response = runtime.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "query_vault_context", "arguments": {"query": "x", "k": 1}},
            }
        )

    assert response is not None
    assert response["error"]["code"] == -32000
    assert "MCP request failed method=tools/call request_id=1 code=-32000 message=Tool execution failed" in caplog.text
