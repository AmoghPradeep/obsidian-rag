from pathlib import Path

from total_recall.background_worker.service import BackgroundWorker
from total_recall.config import AppConfig
from total_recall.mcp_server.tools import MCPTools


def test_image_folder_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    incoming = tmp_path / "incoming"
    audio = incoming / "audio"
    pdf = incoming / "pdf"
    image = incoming / "image"
    text = incoming / "text"
    for p in (vault, audio, pdf, image, text):
        p.mkdir(parents=True, exist_ok=True)

    export_dir = image / "note-1"
    export_dir.mkdir()
    for name in ("image-1-of-3.png", "image-2-of-3.png", "image-3-of-3.png"):
        (export_dir / name).write_bytes(b"fake image")

    cfg = AppConfig(
        vault_path=vault,
        incoming_root=incoming,
        db_path=tmp_path / "db.sqlite3",
        queue_path=tmp_path / "jobs.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )

    monkeypatch.setattr("total_recall.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("total_recall.background_worker.watchers.is_stable_directory", lambda *_args, **_kwargs: True)

    def fake_chat(prompt: str, images=None, require_success=False):
        if "extracting content from a handwritten-notes PDF page image" in prompt:
            page_name = Path(images[0]).name if images else "page"
            return f"- extracted from {page_name}"
        if "reducing per-page extracted notes" in prompt:
            return "Combined summary"
        if "Choose up to 5 domain tags" in prompt:
            return "notes,apple-notes"
        if "Create a normalized Obsidian markdown note" in prompt:
            return '{"fileName":"apple-export","relativePath":"inbox/imported","content":"# Apple Export\\n\\n## 1. Transcript\\nCombined\\n\\n## 2. Summary & Takeaways\\nCombined summary\\n\\n## 3. Tags\\n- notes\\n- apple-notes","tags":["notes","apple-notes"]}'
        return ""

    worker = BackgroundWorker(cfg)
    worker.llm_client.chat = fake_chat

    queued = worker.scan_once()
    assert queued["image_folder"] == 1

    metrics = worker.process_queue_once()
    assert metrics["processed"] == 1
    assert metrics["indexed_chunks"] >= 1

    md = vault / "inbox" / "imported" / "apple-export.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "[[z.rawdata/image_folder/note-1_" in text
    assert "image-1-of-3.png" in text
    assert "image-2-of-3.png" in text
    assert "image-3-of-3.png" in text

    tools = MCPTools(cfg)
    out = tools.query_vault_context("apple export", 5)
    assert out["k"] >= 1
    assert any(row["doc_path"].endswith("apple-export.md") for row in out["results"])
