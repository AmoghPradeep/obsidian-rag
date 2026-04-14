from pathlib import Path

from obsidian_rag_mcp.background_worker.service import BackgroundWorker
from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.mcp_server.tools import MCPTools


def test_image_folder_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    audio = tmp_path / "audio"
    pdf = tmp_path / "pdf"
    images = tmp_path / "images"
    for p in (vault, audio, pdf, images):
        p.mkdir(parents=True, exist_ok=True)

    export_dir = images / "note-1"
    export_dir.mkdir()
    for name in ("image-1-of-3.png", "image-2-of-3.png", "image-3-of-3.png"):
        (export_dir / name).write_bytes(b"fake image")

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
    monkeypatch.setattr("obsidian_rag_mcp.background_worker.watchers.is_stable_directory", lambda *_args, **_kwargs: True)

    def fake_chat(prompt: str, images=None, generation_mode="openai", allow_local_fallback=True, require_success=False):
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
