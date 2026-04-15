from pathlib import Path

from total_recall.background_worker.pdf_pipeline import process_pdf_to_markdown
from total_recall.rag_core.llm_client import OpenAICompatibleClient
from total_recall.rag_core.tags import TagCatalog
from total_recall.rag_core.vector_store.sqlite_store import SQLiteVectorStore


def test_pdf_temp_images_cleaned(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    vault.mkdir(parents=True, exist_ok=True)
    image_base = tmp_path / "temp_images"

    raw_pdf = vault / "z.rawdata" / "pdf" / "doc.pdf"
    raw_pdf.parent.mkdir(parents=True, exist_ok=True)
    raw_pdf.write_bytes(b"pdf")

    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    tag_catalog = TagCatalog(store)
    client = OpenAICompatibleClient("https://api.openai.com/v1", "gpt-5.4-mini")

    monkeypatch.setattr(
        "total_recall.background_worker.pdf_pipeline.convert_pdf_to_jpg_pages",
        lambda _pdf, image_dir: [image_dir / "page-1.jpg"],
    )

    def fake_chat(prompt: str, images=None, require_success=False):
        if "Create a normalized Obsidian markdown note" in prompt:
            return '{"fileName":"doc","relativePath":"inbox/imported","content":"# Title\\n\\n## Source\\n[[z.rawdata/pdf/doc.pdf]]","tags":["notes"]}'
        if "Choose up to 5 domain tags" in prompt:
            return "notes"
        return "ok"

    monkeypatch.setattr(client, "chat", fake_chat)

    result = process_pdf_to_markdown(raw_pdf, vault, image_base, client, tag_catalog)
    assert result.success is True
    assert not any(image_base.glob("pdf-pages-*"))
