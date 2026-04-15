from __future__ import annotations

import logging
import shutil
import tempfile
import time
from pathlib import Path

from total_recall.background_worker.audio_pipeline import process_audio_to_markdown
from total_recall.background_worker.image_folder_pipeline import process_image_folder_to_markdown
from total_recall.background_worker.pdf_pipeline import process_pdf_to_markdown
from total_recall.background_worker.text_pipeline import process_text_to_markdown
from total_recall.background_worker.queue import DurableJobQueue
from total_recall.background_worker.watchers import scan_and_enqueue
from total_recall.config import AppConfig
from total_recall.rag_core.embeddings import EmbeddingService
from total_recall.rag_core.indexing import index_markdown_document
from total_recall.rag_core.llm_client import OpenAICompatibleClient
from total_recall.rag_core.tags import TagCatalog
from total_recall.rag_core.vector_store.sqlite_store import SQLiteVectorStore
from total_recall.background_worker.file_utils import hash_file

LOG = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.queue = DurableJobQueue(config.queue_path)
        self.vector_store = SQLiteVectorStore(config.db_path)
        self.embeddings = EmbeddingService(config.models.api_base_url, config.models.embedding_model)
        self.llm_client = OpenAICompatibleClient(config.models.api_base_url, config.models.generation_model)
        self.tag_catalog = TagCatalog(self.vector_store)
        LOG.info(
            "Initialized background worker vault_path=%s audio_watch_path=%s pdf_watch_path=%s image_watch_path=%s text_watch_path=%s",
            self.config.vault_path,
            self.config.audio_watch_path,
            self.config.pdf_watch_path,
            self.config.image_watch_path,
            self.config.text_watch_path,
        )

    def scan_once(self) -> dict[str, int]:
        LOG.debug("Scanning watch directories for new jobs")
        counts = scan_and_enqueue(
            self.config.audio_watch_path,
            self.config.pdf_watch_path,
            self.config.image_watch_path,
            self.config.text_watch_path,
            self.queue,
            stability_seconds=self.config.watcher_stability_seconds,
        )
        LOG.info("Watcher scan complete counts=%s", counts)
        return counts

    def process_queue_once(self) -> dict[str, int]:
        jobs = self.queue.pop_all()
        LOG.info("Processing queued jobs count=%s", len(jobs))
        metrics = {"processed": 0, "errors": 0, "indexed_chunks": 0}
        for job in jobs:
            source = Path(job.source_path)
            if self.vector_store.match_hash(job.source_path, job.idempotency_key):
                LOG.info("Skipping already indexed job job_type=%s source=%s", job.job_type, source)
                continue

            prepared_source = self._prepare_source(job, source)
            result = self._run_job_with_retry(job.job_type, prepared_source, self.config.vault_path)

            if result.success and result.output_doc:
                try:
                    self.vector_store.upsert_doc_hash(job.source_path, job.idempotency_key)
                    text = result.output_doc.read_text(encoding="utf-8")
                    count = index_markdown_document(
                        result.output_doc,
                        text,
                        self.embeddings,
                        self.vector_store,
                        chunk_size=self.config.chunking.chunk_size,
                        chunk_overlap=self.config.chunking.chunk_overlap,
                    )
                    metrics["indexed_chunks"] += count
                    metrics["processed"] += 1
                    LOG.info(
                        "Indexed processed job job_type=%s source=%s output_doc=%s indexed_chunks=%s",
                        job.job_type,
                        source,
                        result.output_doc,
                        count,
                    )
                except Exception:
                    metrics["errors"] += 1
                    LOG.exception(
                        "Failed to index processed job job_type=%s source=%s output_doc=%s",
                        job.job_type,
                        source,
                        result.output_doc,
                    )
            else:
                metrics["errors"] += 1
                LOG.error(
                    "Job completed with failure job_type=%s source=%s message=%s",
                    job.job_type,
                    source,
                    result.message,
                )
        LOG.info("Finished processing queue metrics=%s", metrics)
        return metrics

    def run_forever(self, poll_seconds: float = 30) -> None:
        while True:
            queued = self.scan_once()
            metrics = self.process_queue_once()
            LOG.info("scan=%s metrics=%s", queued, metrics)
            time.sleep(poll_seconds)

    def _run_job_with_retry(self, job_type: str, source: Path, out_path: Path, retries: int = 2):
        image_dir = Path(tempfile.gettempdir()) / "total_recall_pdf_pages"
        last_result = None
        for attempt in range(retries + 1):
            LOG.info(
                "Running job attempt job_type=%s source=%s attempt=%s max_attempts=%s",
                job_type,
                source,
                attempt + 1,
                retries + 1,
            )
            if job_type == "audio":
                last_result = process_audio_to_markdown(
                    source_audio=source,
                    output_md=out_path,
                    llm_client=self.llm_client,
                    tag_catalog=self.tag_catalog,
                    transcription_model=self.config.models.transcription_model,
                )
            elif job_type == "pdf":
                last_result = process_pdf_to_markdown(
                    source_pdf=source,
                    output_md=out_path,
                    image_dir=image_dir,
                    llm_client=self.llm_client,
                    tag_catalog=self.tag_catalog,
                )
            elif job_type == "image_folder":
                last_result = process_image_folder_to_markdown(
                    source_dir=source,
                    output_md=out_path,
                    llm_client=self.llm_client,
                    tag_catalog=self.tag_catalog,
                )
            elif job_type == "text":
                last_result = process_text_to_markdown(
                    source_text=source,
                    output_md=out_path,
                    llm_client=self.llm_client,
                    tag_catalog=self.tag_catalog,
                )
            else:
                LOG.error("Encountered unsupported job type job_type=%s source=%s", job_type, source)
                raise ValueError(f"unsupported job type: {job_type}")
            if last_result.success:
                LOG.info("Job attempt succeeded job_type=%s source=%s attempt=%s", job_type, source, attempt + 1)
                return last_result
            LOG.warning("Job failed type=%s source=%s attempt=%s", job_type, source, attempt + 1)
        LOG.error("Job exhausted retries job_type=%s source=%s retries=%s", job_type, source, retries + 1)
        return last_result

    def _prepare_source(self, job, source: Path) -> Path:
        raw_root = self.config.vault_path / "z.rawdata" / job.job_type
        raw_root.mkdir(parents=True, exist_ok=True)

        if job.job_type == "image_folder":
            destination = raw_root / f"{source.name}_{job.idempotency_key[:12]}"
            if destination.exists():
                LOG.debug("Replacing existing prepared image folder destination=%s", destination)
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
            LOG.info("Prepared image folder source=%s destination=%s", source, destination)
            return destination

        file_hash = hash_file(source)
        destination = raw_root / f"{source.stem}_{file_hash}{source.suffix}"
        shutil.copy(source, destination)
        LOG.info("Prepared file source=%s destination=%s", source, destination)
        return destination
