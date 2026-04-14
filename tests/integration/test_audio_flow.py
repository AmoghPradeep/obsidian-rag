from pathlib import Path

from obsidian_rag_mcp.background_worker.service import BackgroundWorker
from obsidian_rag_mcp.config import AppConfig


def test_audio_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    audio = tmp_path / "audio"
    pdf = tmp_path / "pdf"
    images = tmp_path / "images"
    for p in (vault, audio, pdf, images):
        p.mkdir(parents=True, exist_ok=True)

    cfg = AppConfig(
        vault_path=vault,
        audio_watch_path=audio,
        pdf_watch_path=pdf,
        image_watch_path=images,
        db_path=tmp_path / "db.sqlite3",
        queue_path=tmp_path / "jobs.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )

    monkeypatch.setattr("obsidian_rag_mcp.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("obsidian_rag_mcp.background_worker.audio_pipeline.compress_for_asr_tempdir", lambda path: path)

    class _FakeTranscriptions:
        def create(self, model: str, file) -> str:
            return "spoken transcript about learning systems"

    class _FakeAudio:
        def __init__(self) -> None:
            self.transcriptions = _FakeTranscriptions()

    class _FakeOpenAI:
        def __init__(self) -> None:
            self.audio = _FakeAudio()

    monkeypatch.setattr("obsidian_rag_mcp.background_worker.audio_pipeline.OpenAI", _FakeOpenAI)

    (audio / "note.m4a").write_bytes(b"fake audio")
    worker = BackgroundWorker(cfg)
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
