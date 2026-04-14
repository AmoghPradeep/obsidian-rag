from pathlib import Path

from obsidian_rag_mcp.background_worker.watchers import (
    compute_directory_idempotency_key,
    is_stable_directory,
    list_supported_image_files,
)


def test_supported_images_use_natural_filename_order(tmp_path: Path) -> None:
    folder = tmp_path / "note-1"
    folder.mkdir()
    for name in ("image-10-of-12.png", "image-2-of-12.png", "image-1-of-12.png", "notes.txt"):
        (folder / name).write_bytes(b"x")

    ordered = [path.name for path in list_supported_image_files(folder)]
    assert ordered == ["image-1-of-12.png", "image-2-of-12.png", "image-10-of-12.png"]


def test_directory_idempotency_changes_when_member_file_changes(tmp_path: Path) -> None:
    folder = tmp_path / "note-1"
    folder.mkdir()
    image = folder / "image-1-of-1.png"
    image.write_bytes(b"first")

    before = compute_directory_idempotency_key(folder)
    image.write_bytes(b"second")
    after = compute_directory_idempotency_key(folder)

    assert before != after


def test_unstable_directory_is_detected(tmp_path: Path, monkeypatch) -> None:
    folder = tmp_path / "note-1"
    folder.mkdir()
    image = folder / "image-1-of-1.png"
    image.write_bytes(b"first")

    def mutate(_seconds: float) -> None:
        image.write_bytes(b"second")

    monkeypatch.setattr("obsidian_rag_mcp.background_worker.watchers.time.sleep", mutate)
    assert is_stable_directory(folder, wait_seconds=0.01) is False
