from pathlib import Path

from total_recall.background_worker.write_markdown import FALLBACK_RELATIVE_DIR, process_json_response


def test_path_safety_integration_blocks_absolute_like_paths(tmp_path: Path) -> None:
    payload = '{"fileName":"Unsafe","relativePath":"/root/escape","content":"# X","tags":[]}'
    file_path, _ = process_json_response(payload, tmp_path)
    assert file_path.exists()
    assert file_path.parent == (tmp_path / FALLBACK_RELATIVE_DIR)
