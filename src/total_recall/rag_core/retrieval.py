from __future__ import annotations

from total_recall.rag_core.embeddings import EmbeddingService
from total_recall.rag_core.vector_store.base import VectorStore


class RetrievalService:
    def __init__(self, embeddings: EmbeddingService, vector_store: VectorStore, min_k: int = 1, max_k: int = 20) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.min_k = min_k
        self.max_k = max_k

    def query(self, text: str, k: int) -> list[dict]:
        if not text.strip():
            raise ValueError("query text is required")
        k = max(self.min_k, min(self.max_k, k))
        vector = self.embeddings.embed_texts([text])[0]
        rows = self.vector_store.query(vector, k)
        return [
            {
                "chunk_id": r.chunk_id,
                "doc_path": r.doc_path,
                "content": r.content,
                "score": r.score,
            }
            for r in rows
        ]
