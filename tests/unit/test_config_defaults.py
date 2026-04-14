from pathlib import Path

from obsidian_rag_mcp.config import default_runtime_paths


def test_linux_default_runtime_paths_are_linux_friendly() -> None:
    paths = default_runtime_paths(home=Path("/home/alice"), platform_name="posix")
    assert paths["vault_path"] == Path("/home/alice/Documents/obsidian-rag-vault")
    assert paths["image_watch_path"] == Path("/home/alice/.obragconfig/incoming/images")
    assert paths["db_path"] == Path("/home/alice/.obragconfig/data/rag.sqlite3")


def test_windows_default_runtime_paths_remain_home_relative() -> None:
    paths = default_runtime_paths(home=Path("C:/Users/Alice"), platform_name="nt")
    assert paths["vault_path"] == Path("C:/Users/Alice/Documents/obsidian-rag-vault")
    assert paths["image_watch_path"] == Path("C:/Users/Alice/.obragconfig/incoming/images")
