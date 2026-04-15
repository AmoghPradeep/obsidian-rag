from __future__ import annotations

import hashlib
from typing import Iterable

from total_recall.models import Chunk


def chunk_text(text: str, doc_path: str, chunk_size: int = 800, chunk_overlap: int = 120) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >=0 and < chunk_size")

    words = text.split()
    if not words:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[Chunk] = []
    idx = 0
    pos = 0
    while idx < len(words):
        window = words[idx : idx + chunk_size]
        content = " ".join(window)
        raw = f"{doc_path}:{pos}:{content}"
        chunk_id = hashlib.sha1(raw.encode("utf-8")).hexdigest()
        chunks.append(Chunk(chunk_id=chunk_id, doc_path=doc_path, content=content, position=pos))
        pos += 1
        idx += step
    return chunks
