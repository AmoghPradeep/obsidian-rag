from pathlib import Path

from total_recall.background_worker.queue import DurableJobQueue, IngestionJob


def test_idempotent_enqueue(tmp_path: Path) -> None:
    queue = DurableJobQueue(tmp_path / "jobs.jsonl")
    job = IngestionJob(job_type="audio", source_path="a.m4a", idempotency_key="k1")
    assert queue.enqueue(job) is True
    assert queue.enqueue(job) is False
    popped = queue.pop_all()
    assert len(popped) == 1
