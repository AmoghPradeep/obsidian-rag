import json
import logging
import re
from pathlib import Path

LOG = logging.getLogger(__name__)
FALLBACK_RELATIVE_DIR = Path("inbox") / "imported"


def _safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", name)
    name = re.sub(r"\s+", " ", name)
    cleaned = name[:150].strip(" .")
    return cleaned or "Untitled Note"


def _safe_segment(segment: str) -> str:
    segment = segment.strip()
    segment = re.sub(r'[<>:"\\|?*\x00-\x1f]', "-", segment)
    segment = re.sub(r"\s+", " ", segment)
    segment = segment.strip(" .")
    return segment


def sanitize_relative_dir(raw_relative_path: object) -> tuple[Path, bool, str]:
    """
    Return (relative_dir, used_fallback, reason).
    """
    if not isinstance(raw_relative_path, str):
        return FALLBACK_RELATIVE_DIR, True, "relativePath missing or non-string"

    proposed = raw_relative_path.strip()
    if not proposed:
        return FALLBACK_RELATIVE_DIR, True, "relativePath empty"

    normalized = proposed.replace("\\", "/")
    lowered = normalized.lower()

    is_absolute_like = (
        bool(re.match(r"^[a-zA-Z]:", normalized))
        or normalized.startswith("/")
        or normalized.startswith("//")
        or normalized.startswith("\\\\")
        or bool(re.match(r"^[a-zA-Z]--", normalized))
        or lowered.startswith("c--users")
    )
    if is_absolute_like:
        return FALLBACK_RELATIVE_DIR, True, f"absolute or malformed path: {proposed}"

    parts: list[str] = []
    for raw_part in normalized.split("/"):
        part = raw_part.strip()
        if not part or part == ".":
            continue
        if part == "..":
            return FALLBACK_RELATIVE_DIR, True, f"path traversal segment in: {proposed}"
        safe = _safe_segment(part)
        if safe:
            parts.append(safe)

    if not parts:
        return FALLBACK_RELATIVE_DIR, True, "relativePath sanitized to empty"

    return Path(*parts), False, ""


def resolve_safe_output_dir(vault_root: Path, raw_relative_path: object) -> tuple[Path, bool]:
    relative_dir, used_fallback, reason = sanitize_relative_dir(raw_relative_path)
    vault_root_resolved = vault_root.resolve()
    candidate = (vault_root_resolved / relative_dir).resolve()

    try:
        candidate.relative_to(vault_root_resolved)
    except ValueError:
        used_fallback = True
        reason = reason or f"out-of-vault path after resolve: {candidate}"
        candidate = (vault_root_resolved / FALLBACK_RELATIVE_DIR).resolve()

    if used_fallback:
        LOG.warning("Using fallback markdown destination due to invalid relativePath: %s", reason)

    candidate.mkdir(parents=True, exist_ok=True)
    return candidate, used_fallback


def process_json_response(json_parameters: str, obsidian_vault_path: Path) -> tuple[Path, list[str]]:
    """
    Parses LLM JSON output and creates a markdown file in the given Obsidian vault.

    Args:
        json_parameters (str): JSON string from LLM containing `fileName` and `content`
        obsidian_vault_path (str): Path to your Obsidian vault directory

    Returns:
        Path: Full path of the created markdown file
    """

    # Clean possible markdown fences
    cleaned = json_parameters.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    # Parse JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON input: {e}")

    # Extract fields
    file_name = _safe_filename(str(data.get("fileName", "Untitled Note")))
    output_dir, _ = resolve_safe_output_dir(obsidian_vault_path, data.get("relativePath", ""))

    content = data.get("content", "")
    tags = data.get("tags", [])

    if not isinstance(tags, list):
        raise ValueError("Tags must be a list")

    tags = [str(tag).strip() for tag in tags if str(tag).strip()]

    if not content:
        raise ValueError("Content is empty. Cannot create markdown file.")

    # Create file path
    file_path = output_dir / f"{file_name}.md"

    # Avoid overwriting existing files
    counter = 1
    while file_path.exists():
        file_path = output_dir / f"{file_name} {counter}.md"
        counter += 1

    # Write file
    file_path.write_text(content, encoding="utf-8")

    return file_path, tags
