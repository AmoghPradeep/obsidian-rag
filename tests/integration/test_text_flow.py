from pathlib import Path

from total_recall.background_worker.service import BackgroundWorker
from total_recall.config import AppConfig


def test_text_ingestion_end_to_end_for_txt_and_md(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    incoming = tmp_path / "incoming"
    audio = incoming / "audio"
    pdf = incoming / "pdf"
    image = incoming / "image"
    text = incoming / "text"
    for path in (vault, audio, pdf, image, text):
        path.mkdir(parents=True, exist_ok=True)

    cfg = AppConfig(
        vault_path=vault,
        incoming_root=incoming,
        db_path=tmp_path / "db.sqlite3",
        queue_path=tmp_path / "jobs.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )

    monkeypatch.setattr("total_recall.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("total_recall.background_worker.service.hash_file", lambda path: f"fakehash-{path.stem}")

    (text / "ideas.txt").write_text("rough notes about learning systems", encoding="utf-8")
    (text / "source.md").write_text("# Existing Note\n\nThoughts about retrieval", encoding="utf-8")

    def fake_chat(prompt: str, images=None, require_success=False):
        if "raw text file" in prompt and "rough notes about learning systems" in prompt:
            return '{"fileName":"ideas note","relativePath":"inbox/imported","content":"# Ideas Note\\n\\n## 1. Transcript\\nrough notes about learning systems\\n\\n## 2. Summary & Takeaways\\n- learning systems\\n\\n## 3. Tags\\n- learning\\n\\n## 4. Resources\\n- [[z.rawdata/text/ideas_fakehash-ideas.txt]]","tags":["learning"]}'
        if "raw text file" in prompt and "# Existing Note" in prompt:
            return '{"fileName":"source note","relativePath":"inbox/imported","content":"# Source Note\\n\\n## 1. Transcript\\nThoughts about retrieval\\n\\n## 2. Summary & Takeaways\\n- retrieval\\n\\n## 3. Tags\\n- retrieval\\n\\n## 4. Resources\\n- [[z.rawdata/text/source_fakehash-source.md]]","tags":["retrieval"]}'
        return ""

    worker = BackgroundWorker(cfg)
    worker.llm_client.chat = fake_chat

    queued = worker.scan_once()
    assert queued["text"] == 2

    metrics = worker.process_queue_once()
    assert metrics["processed"] == 2
    assert metrics["indexed_chunks"] >= 2

    txt_raw = vault / "z.rawdata" / "text" / "ideas_fakehash-ideas.txt"
    md_raw = vault / "z.rawdata" / "text" / "source_fakehash-source.md"
    assert txt_raw.exists()
    assert md_raw.exists()

    txt_note = vault / "inbox" / "imported" / "ideas note.md"
    md_note = vault / "inbox" / "imported" / "source note.md"
    assert txt_note.exists()
    assert md_note.exists()
    assert "[[z.rawdata/text/ideas_fakehash-ideas.txt]]" in txt_note.read_text(encoding="utf-8")
    assert "[[z.rawdata/text/source_fakehash-source.md]]" in md_note.read_text(encoding="utf-8")
