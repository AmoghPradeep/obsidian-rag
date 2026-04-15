from pathlib import Path

from total_recall.background_worker.service import BackgroundWorker
from total_recall.config import AppConfig


def test_pdf_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
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

    monkeypatch.setattr("total_recall.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "total_recall.background_worker.pdf_pipeline.convert_pdf_to_jpg_pages",
        lambda _pdf, image_dir: [image_dir / "page-1.jpg"],
    )

    def fake_chat(prompt: str, images=None, require_success=False):
        if "extracting content from a handwritten-notes PDF page image" in prompt:
            return "- handwritten bullet"
        if "reducing per-page extracted notes" in prompt:
            return "Short summary"
        if "Choose up to 5 domain tags" in prompt:
            return "notes,learning"
        if "Create a normalized Obsidian markdown note" in prompt:
            return '{"fileName":"handwritten","relativePath":"inbox/imported","content":"# Title\\n\\n## Extracted Notes\\n- handwritten bullet\\n\\n## Summary\\nShort summary\\n\\n## Source\\n[[z.rawdata/pdf/handwritten_fakehash.pdf]]","tags":["notes","learning"]}'
        return ""

    (pdf / "handwritten.pdf").write_bytes(b"fake pdf")
    worker = BackgroundWorker(cfg)
    worker.llm_client.chat = fake_chat

    # keep deterministic hash/copy filename for backlink assertion
    monkeypatch.setattr("total_recall.background_worker.service.hash_file", lambda _p: "fakehash")

    queued = worker.scan_once()
    assert queued["pdf"] == 1
    assert queued["image_folder"] == 0
    assert queued["text"] == 0
    metrics = worker.process_queue_once()
    assert metrics["processed"] == 1

    copied_raw = vault / "z.rawdata" / "pdf" / "handwritten_fakehash.pdf"
    assert copied_raw.exists()

    md = vault / "inbox" / "imported" / "handwritten.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "[[z.rawdata/pdf/handwritten_fakehash.pdf]]" in text
