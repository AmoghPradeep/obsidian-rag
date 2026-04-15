from pathlib import Path

from obsidian_rag_mcp.background_worker.queue import DurableJobQueue
from obsidian_rag_mcp.background_worker.watchers import list_supported_text_files, scan_and_enqueue


def test_supported_text_files_include_txt_and_md_only(tmp_path: Path) -> None:
    folder = tmp_path / "text"
    folder.mkdir()
    for name in ("b.md", "a.txt", "ignore.pdf", "skip.png"):
        (folder / name).write_text("x", encoding="utf-8")

    ordered = [path.name for path in list_supported_text_files(folder)]
    assert ordered == ["a.txt", "b.md"]


def test_scan_and_enqueue_queues_text_files(tmp_path: Path, monkeypatch) -> None:
    queue = DurableJobQueue(tmp_path / "jobs.jsonl")
    audio = tmp_path / "audio"
    pdf = tmp_path / "pdf"
    images = tmp_path / "images"
    text = tmp_path / "text"
    for path in (audio, pdf, images, text):
        path.mkdir()

    (text / "ideas.txt").write_text("ideas", encoding="utf-8")
    (text / "note.md").write_text("# note", encoding="utf-8")

    monkeypatch.setattr("obsidian_rag_mcp.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)

    counts = scan_and_enqueue(audio, pdf, images, text, queue, stability_seconds=0.01)

    assert counts["text"] == 2
    jobs = queue.pop_all()
    assert [job.job_type for job in jobs] == ["text", "text"]
    assert sorted(Path(job.source_path).name for job in jobs) == ["ideas.txt", "note.md"]
