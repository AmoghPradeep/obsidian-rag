from __future__ import annotations

import hashlib
import logging
import re
import time
from pathlib import Path

from obsidian_rag_mcp.background_worker.file_utils import hash_file
from obsidian_rag_mcp.background_worker.queue import DurableJobQueue, IngestionJob

LOG = logging.getLogger(__name__)
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def compute_idempotency_key(path: Path) -> str:
    st = path.stat()
    raw = f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_directory_idempotency_key(path: Path) -> str:
    digest = hashlib.sha256(str(path.resolve()).encode("utf-8"))
    for image in list_supported_image_files(path):
        rel = image.relative_to(path).as_posix()
        st = image.stat()
        digest.update(rel.encode("utf-8"))
        digest.update(str(st.st_size).encode("utf-8"))
        digest.update(str(st.st_mtime_ns).encode("utf-8"))
        digest.update(hash_file(image).encode("utf-8"))
    return digest.hexdigest()


def is_stable_file(path: Path, wait_seconds: float = 1.5) -> bool:
    first = path.stat()
    time.sleep(wait_seconds)
    second = path.stat()
    return first.st_size == second.st_size and first.st_mtime_ns == second.st_mtime_ns


def list_supported_image_files(path: Path) -> list[Path]:
    return sorted(
        [
            child
            for child in path.iterdir()
            if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        ],
        key=_natural_sort_key,
    )


def is_stable_directory(path: Path, wait_seconds: float = 1.5) -> bool:
    first = _directory_snapshot(path)
    time.sleep(wait_seconds)
    second = _directory_snapshot(path)
    return first == second


def scan_and_enqueue(
    audio_dir: Path,
    pdf_dir: Path,
    image_dir: Path,
    queue: DurableJobQueue,
    stability_seconds: float = 1.5,
) -> dict[str, int]:
    counts = {"audio": 0, "pdf": 0, "image_folder": 0}
    for ext, folder, kind in (("*.m4a", audio_dir, "audio"), ("*.pdf", pdf_dir, "pdf")):
        if not folder.exists():
            continue
        for file in folder.glob(ext):
            if not is_stable_file(file, wait_seconds=stability_seconds):
                continue
            job = IngestionJob(job_type=kind, source_path=str(file), idempotency_key=compute_idempotency_key(file))
            if queue.enqueue(job):
                counts[kind] += 1

    if not image_dir.exists():
        return counts
    for folder in sorted((p for p in image_dir.iterdir() if p.is_dir()), key=lambda p: p.name.lower()):
        images = list_supported_image_files(folder)
        if not images:
            LOG.warning("Skipping image folder without supported images: %s", folder)
            continue
        if not is_stable_directory(folder, wait_seconds=stability_seconds):
            LOG.info("Deferring unstable image folder: %s", folder)
            continue
        job = IngestionJob(
            job_type="image_folder",
            source_path=str(folder),
            idempotency_key=compute_directory_idempotency_key(folder),
        )
        if queue.enqueue(job):
            counts["image_folder"] += 1
    return counts


def _directory_snapshot(path: Path) -> list[tuple[str, int, int]]:
    snapshot: list[tuple[str, int, int]] = []
    for image in list_supported_image_files(path):
        st = image.stat()
        snapshot.append((image.name, st.st_size, st.st_mtime_ns))
    return snapshot


def _natural_sort_key(path: Path) -> tuple[object, ...]:
    parts = re.split(r"(\d+)", path.name.lower())
    key: list[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return tuple(key)
