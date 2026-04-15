from pathlib import Path

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.config import default_runtime_paths


def test_linux_default_runtime_paths_are_linux_friendly() -> None:
    paths = default_runtime_paths(home=Path("/home/alice"), platform_name="posix")
    assert paths["vault_path"] == Path("/home/alice/Documents/obsidian-rag-vault")
    assert paths["incoming_root"] == Path("/home/alice/.obragconfig/incoming")
    assert paths["db_path"] == Path("/home/alice/.obragconfig/data/rag.sqlite3")


def test_windows_default_runtime_paths_remain_home_relative() -> None:
    paths = default_runtime_paths(home=Path("C:/Users/Alice"), platform_name="nt")
    assert paths["vault_path"] == Path("C:/Users/Alice/Documents/obsidian-rag-vault")
    assert paths["incoming_root"] == Path("C:/Users/Alice/.obragconfig/incoming")


def test_default_model_config_is_api_only() -> None:
    cfg = AppConfig()
    assert cfg.models.api_base_url == "https://api.openai.com/v1"
    assert cfg.models.transcription_model == "gpt-4o-mini-transcribe"
    assert cfg.models.embedding_model == "text-embedding-3-large"
