from pathlib import Path

from obsidian_rag_mcp.background_worker.service import BackgroundWorker
from obsidian_rag_mcp.config import AppConfig


def test_audio_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    incoming = tmp_path / "incoming"
    audio = incoming / "audio"
    pdf = incoming / "pdf"
    image = incoming / "image"
    text = incoming / "text"
    for p in (vault, audio, pdf, image, text):
        p.mkdir(parents=True, exist_ok=True)

    cfg = AppConfig(
        vault_path=vault,
        incoming_root=incoming,
        db_path=tmp_path / "db.sqlite3",
        queue_path=tmp_path / "jobs.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )

    monkeypatch.setattr("obsidian_rag_mcp.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("obsidian_rag_mcp.background_worker.audio_pipeline.compress_for_asr_tempdir", lambda path: path)

    (audio / "note.m4a").write_bytes(b"fake audio")
    worker = BackgroundWorker(cfg)
    worker.llm_client.transcribe_audio = lambda *_args, **_kwargs: "spoken transcript about learning systems"
    worker.llm_client.chat = lambda *_args, **_kwargs: (
        '{"fileName":"note","relativePath":"inbox/imported","content":"# Summary\\n\\nspoken transcript about learning systems\\n\\ntags: learning,systems","tags":["learning","systems"]}'
    )

    queued = worker.scan_once()
    assert queued["audio"] == 1
    metrics = worker.process_queue_once()
    assert metrics["processed"] == 1

    md = vault / "inbox" / "imported" / "note.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "# Summary" in text
    assert "tags:" in text
