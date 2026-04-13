from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ENV_DIR = Path.home() / ".obragconfig"
DEFAULT_ENV_FILE = DEFAULT_ENV_DIR / ".env"


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
    vault_path: Path = Field(default=Path(r"C:\Users\Welcome\Documents\amogh-brain"))
    audio_watch_path: Path = Field(default=Path("./incoming/audio"))
    pdf_watch_path: Path = Field(default=Path("./incoming/pdf"))
    db_path: Path = Field(default=Path("./data/rag.sqlite3"))
    manifest_path: Path = Field(default=Path("./data/manifest.json"))
    queue_path: Path = Field(default=Path("./data/jobs.jsonl"))
    log_level: str = "INFO"
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)


def load_config() -> AppConfig:
    DEFAULT_ENV_DIR.mkdir(parents=True, exist_ok=True)
    cfg = AppConfig()
    cfg.vault_path.mkdir(parents=True, exist_ok=True)
    cfg.audio_watch_path.mkdir(parents=True, exist_ok=True)
    cfg.pdf_watch_path.mkdir(parents=True, exist_ok=True)
    cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.queue_path.parent.mkdir(parents=True, exist_ok=True)
    return cfg
