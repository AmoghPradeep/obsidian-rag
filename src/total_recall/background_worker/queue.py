from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock

LOG = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionJob:
    job_type: str
    source_path: str
    idempotency_key: str


class DurableJobQueue:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._seen_keys: set[str] = set()
        self._load_seen_keys()
        LOG.debug("Initialized durable job queue path=%s seen_keys=%s", self.path, len(self._seen_keys))

    def _load_seen_keys(self) -> None:
        if not self.path.exists():
            LOG.debug("Queue file does not exist yet path=%s", self.path)
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            self._seen_keys.add(row["idempotency_key"])
        LOG.debug("Loaded existing queue state path=%s seen_keys=%s", self.path, len(self._seen_keys))

    def enqueue(self, job: IngestionJob) -> bool:
        with self._lock:
            if job.idempotency_key in self._seen_keys:
                LOG.debug(
                    "Skipping duplicate queue entry job_type=%s source=%s idempotency_key=%s",
                    job.job_type,
                    job.source_path,
                    job.idempotency_key,
                )
                return False
            self._seen_keys.add(job.idempotency_key)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(job)) + "\n")
        LOG.info("Enqueued job job_type=%s source=%s", job.job_type, job.source_path)
        return True

    def pop_all(self) -> list[IngestionJob]:
        with self._lock:
            if not self.path.exists():
                LOG.debug("No queue file present during pop path=%s", self.path)
                return []
            jobs: list[IngestionJob] = []
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                data = json.loads(line)
                jobs.append(IngestionJob(**data))
            self.path.write_text("", encoding="utf-8")
            LOG.info("Popped queued jobs count=%s path=%s", len(jobs), self.path)
            return jobs
