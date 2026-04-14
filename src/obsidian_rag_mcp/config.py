from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ENV_DIR = Path.home() / ".obragconfig"
DEFAULT_ENV_FILE = DEFAULT_ENV_DIR / ".env"


def default_runtime_paths(
    *,
    home: Path | None = None,
    platform_name: str | None = None,
) -> dict[str, Path]:
    resolved_home = home or Path.home()
    resolved_platform = (platform_name or os.name).lower()

    config_root = resolved_home / ".obragconfig"
    documents_root = resolved_home / "Documents"
    if resolved_platform == "nt":
        documents_root = resolved_home / "Documents"

    return {
        "config_root": config_root,
        "vault_path": documents_root / "obsidian-rag-vault",
        "audio_watch_path": config_root / "incoming" / "audio",
        "pdf_watch_path": config_root / "incoming" / "pdf",
        "image_watch_path": config_root / "incoming" / "images",
        "db_path": config_root / "data" / "rag.sqlite3",
        "manifest_path": config_root / "data" / "manifest.json",
        "queue_path": config_root / "data" / "jobs.jsonl",
    }


class ChunkingConfig(BaseModel):
    chunk_size: int = 800
    chunk_overlap: int = 120


class ModelConfig(BaseModel):
    asr_model: str = "cohere-transcribe-03-2026"
    generation_model: str = "gemma4-26B-A4B"
    generation_quant: str = "Q3_K_M"
    embedding_model: str = "Qwen3-Embedding-0.6B"
    llm_service_url: str = "http://localhost:1234"


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OBRAG_",
        env_file=str(DEFAULT_ENV_FILE),
        env_nested_delimiter="__",
        extra="ignore",
    )

    transcribe_local: bool = Field(default=False)
    vault_path: Path = Field(default_factory=lambda: default_runtime_paths()["vault_path"])
    audio_watch_path: Path = Field(default_factory=lambda: default_runtime_paths()["audio_watch_path"])
    pdf_watch_path: Path = Field(default_factory=lambda: default_runtime_paths()["pdf_watch_path"])
    image_watch_path: Path = Field(default_factory=lambda: default_runtime_paths()["image_watch_path"])
    db_path: Path = Field(default_factory=lambda: default_runtime_paths()["db_path"])
    manifest_path: Path = Field(default_factory=lambda: default_runtime_paths()["manifest_path"])
    queue_path: Path = Field(default_factory=lambda: default_runtime_paths()["queue_path"])
    watcher_stability_seconds: float = 1.5
    log_level: str = "INFO"
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)


def load_config() -> AppConfig:
    DEFAULT_ENV_DIR.mkdir(parents=True, exist_ok=True)
    cfg = AppConfig()
    cfg.vault_path.mkdir(parents=True, exist_ok=True)
    cfg.audio_watch_path.mkdir(parents=True, exist_ok=True)
    cfg.pdf_watch_path.mkdir(parents=True, exist_ok=True)
    cfg.image_watch_path.mkdir(parents=True, exist_ok=True)
    cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.queue_path.parent.mkdir(parents=True, exist_ok=True)
    return cfg
