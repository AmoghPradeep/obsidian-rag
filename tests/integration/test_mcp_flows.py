from pathlib import Path

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.mcp_server.tools import MCPTools


def test_mcp_reindex_and_query(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    audio = tmp_path / "audio"
    pdf = tmp_path / "pdf"
    images = tmp_path / "images"
    for p in (vault, audio, pdf, images):
        p.mkdir(parents=True, exist_ok=True)

    (vault / "note.md").write_text("# Content\nTransformers and attention mechanisms", encoding="utf-8")

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
    reindex = tools.reindex_vault_delta()
    assert reindex["processed"] == 1

    out = tools.query_vault_context("attention", 5)
    assert out["k"] >= 1
    assert out["results"][0]["doc_path"].endswith("note.md")
