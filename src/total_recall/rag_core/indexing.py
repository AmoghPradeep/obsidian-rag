from __future__ import annotations

import logging
from pathlib import Path

from total_recall.rag_core.chunking import chunk_text
from total_recall.rag_core.embeddings import EmbeddingService
from total_recall.rag_core.vector_store.base import VectorStore

LOG = logging.getLogger(__name__)


def index_markdown_document(
    doc_path: Path,
    content: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    LOG.debug("Indexing markdown document path=%s chunk_size=%s chunk_overlap=%s", doc_path, chunk_size, chunk_overlap)
    chunks = chunk_text(content, str(doc_path), chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        vector_store.delete_by_doc(str(doc_path))
        LOG.info("No chunks produced for markdown document path=%s", doc_path)
        return 0
    vectors = embedding_service.embed_texts([c.content for c in chunks])
    vector_store.delete_by_doc(str(doc_path))
    vector_store.upsert_chunks(chunks, vectors)
    LOG.info("Indexed markdown document path=%s chunk_count=%s", doc_path, len(chunks))
    return len(chunks)
