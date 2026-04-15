from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    doc_path: str
    content: str
    position: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: str
    doc_path: str
    content: str
    score: float


@dataclass(slots=True)
class JobResult:
    source_path: Path
    success: bool
    message: str
    output_doc: Path | None = None
