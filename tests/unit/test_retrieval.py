from pathlib import Path

import pytest

from total_recall.rag_core.embeddings import EmbeddingService
from total_recall.rag_core.retrieval import RetrievalService
from total_recall.rag_core.vector_store.sqlite_store import SQLiteVectorStore
from total_recall.models import Chunk


def test_retrieval_clamps_k(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    chunk = Chunk(chunk_id="1", doc_path="d.md", content="hello world", position=0)
    store.upsert_chunks([chunk], [[0.1] * 64])
    emb = EmbeddingService("https://api.openai.com/v1", "x")
    svc = RetrievalService(emb, store, min_k=1, max_k=2)
    out = svc.query("hello", 99)
    assert len(out) <= 2


def test_retrieval_requires_query(tmp_path: Path) -> None:
    store = SQLiteVectorStore(tmp_path / "db.sqlite3")
    emb = EmbeddingService("https://api.openai.com/v1", "x")
    svc = RetrievalService(emb, store)
    with pytest.raises(ValueError):
        svc.query("   ", 3)
