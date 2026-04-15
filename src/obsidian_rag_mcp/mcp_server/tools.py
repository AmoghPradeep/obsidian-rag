from __future__ import annotations

import logging
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.rag_core.embeddings import EmbeddingService
from obsidian_rag_mcp.rag_core.indexing import index_markdown_document
from obsidian_rag_mcp.rag_core.manifest import VaultManifest, compute_vault_fingerprints
from obsidian_rag_mcp.rag_core.retrieval import RetrievalService
from obsidian_rag_mcp.rag_core.vector_store.sqlite_store import SQLiteVectorStore

LOG = logging.getLogger(__name__)


@dataclass(slots=True)
class ReindexResult:
    processed: int
    skipped: int
    deleted: int
    errors: int


class MCPTools:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = SQLiteVectorStore(config.db_path)
        self.embeddings = EmbeddingService(config.models.api_base_url, config.models.embedding_model)
        self.manifest = VaultManifest(config.manifest_path)
        self.retrieval = RetrievalService(self.embeddings, self.store)

    def reindex_vault_delta(self) -> dict:
        LOG.info("Starting vault delta reindex vault_path=%s", self.config.vault_path)
        previous = self.manifest.load()
        current = compute_vault_fingerprints(self.config.vault_path)

        prev_paths = set(previous)
        curr_paths = set(current)

        deleted = prev_paths - curr_paths
        new_or_changed = {p for p in curr_paths if previous.get(p) != current[p]}

        metrics = ReindexResult(processed=0, skipped=0, deleted=0, errors=0)

        for path in sorted(deleted):
            self.store.delete_by_doc(path)
            metrics.deleted += 1
            LOG.info("Removed deleted document from index path=%s", path)

        for path in sorted(new_or_changed):
            try:
                md_path = Path(path)
                content = md_path.read_text(encoding="utf-8")
                count = index_markdown_document(
                    md_path,
                    content,
                    self.embeddings,
                    self.store,
                    chunk_size=self.config.chunking.chunk_size,
                    chunk_overlap=self.config.chunking.chunk_overlap,
                )
                if count > 0:
                    metrics.processed += 1
                    LOG.info("Reindexed markdown document path=%s chunk_count=%s", md_path, count)
                else:
                    metrics.skipped += 1
                    LOG.info("Skipped empty markdown document during reindex path=%s", md_path)
            except Exception:
                metrics.errors += 1
                LOG.exception("Failed to reindex markdown document path=%s", path)

        for path in sorted(curr_paths - new_or_changed):
            metrics.skipped += 1

        self.manifest.save(current)
        LOG.info("Completed vault delta reindex metrics=%s", asdict(metrics))
        return asdict(metrics)

    def query_vault_context(self, query: str, k: int = 5) -> dict:
        LOG.info("Querying vault context query_length=%s requested_k=%s", len(query.strip()), k)
        results = self.retrieval.query(query, k)
        normalized = []
        for row in results:
            normalized.append(
                {
                    "chunk_id": row["chunk_id"],
                    "content": row["content"],
                    "doc_path": row["doc_path"],
                    "score": float(row["score"]),
                    "source": {"doc_path": row["doc_path"], "chunk_id": row["chunk_id"]},
                    "similarity_score": float(row["score"]),
                }
            )
        LOG.info("Completed vault context query returned_k=%s", len(normalized))
        return {"k": len(normalized), "results": normalized}
