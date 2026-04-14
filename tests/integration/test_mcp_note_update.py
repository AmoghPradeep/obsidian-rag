from pathlib import Path

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.mcp_server.tools import MCPTools


def test_update_markdown_note_flow(tmp_path: Path, monkeypatch) -> None:
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

    def fake_chat(prompt: str, images=None, generation_mode="openai", allow_local_fallback=True, require_success=False):
        if "Pick the best markdown file" in prompt:
            return '{"selected_path":"' + str(target).replace('\\', '\\\\') + '","confidence":0.95}'
        if "Summarize this markdown note" in prompt:
            return "- concise summary"
        if "Return up to 8 broad knowledge-domain tags" in prompt:
            return "learning,notes"
        if "Select the best vault-relative directory" in prompt:
            return "knowledge/notes"
        return ""

    monkeypatch.setattr(tools.llm_client, "chat", fake_chat)

    out = tools.update_markdown_note("my note", "organize it")

    assert out["status"] == "updated"
    assert out["moved"] is True

    new_path = Path(out["new_path"])
    assert new_path.exists()
    text = new_path.read_text(encoding="utf-8")
    assert "Original body content." in text
    assert "## Summary" in text
    assert "## Tags" in text


def test_update_markdown_note_ambiguous_no_change(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    audio = tmp_path / "audio"
    pdf = tmp_path / "pdf"
    images = tmp_path / "images"
    for p in (vault, audio, pdf, images):
        p.mkdir(parents=True, exist_ok=True)

    a = vault / "alpha.md"
    b = vault / "alpha copy.md"
    a.write_text("# A", encoding="utf-8")
    b.write_text("# B", encoding="utf-8")

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

    monkeypatch.setattr(tools.llm_client, "chat", lambda *args, **kwargs: '{"selected_path":"","confidence":0.2}')
    out = tools.update_markdown_note("alpha", "")

    assert out["status"] == "ambiguous"
    assert out["changes_applied"] is False
    assert a.read_text(encoding="utf-8") == "# A"
    assert b.read_text(encoding="utf-8") == "# B"
