import json
import re
from pathlib import Path


def     process_json_response(json_parameters: str, obsidian_vault_path: Path) -> tuple[Path, list[str]]:
    """
    Parses LLM JSON output and creates a markdown file in the given Obsidian vault.

    Args:
        json_parameters (str): JSON string from LLM containing `fileName` and `content`
        obsidian_vault_path (str): Path to your Obsidian vault directory

    Returns:
        Path: Full path of the created markdown file
    """

    def safe_filename(name: str) -> str:
        name = name.strip()
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', name)  # remove invalid chars
        name = re.sub(r'\s+', ' ', name)
        return name[:150].strip(" .")

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
    file_name = safe_filename(data.get("fileName", "Untitled Note"))
    path = safe_filename(data.get("relativePath", obsidian_vault_path))

    if not Path(path).is_absolute():
        path = obsidian_vault_path / path

    content = data.get("content", "")
    tags = data.get("tags", [])

    if not isinstance(tags, list):
        raise ValueError("Tags must be a list")

    tags = [str(tag).strip() for tag in tags if str(tag).strip()]

    if not content:
        raise ValueError("Content is empty. Cannot create markdown file.")

    # Ensure vault path exists
    vault_path = path
    vault_path.mkdir(parents=True, exist_ok=True)

    # Create file path
    if path.suffix.lower() != ".md":
        file_path = vault_path / f"{file_name}.md"

    # Avoid overwriting existing files
    counter = 1
    while file_path.exists():
        file_path = vault_path / f"{file_name} {counter}.md"
        counter += 1

    # Write file
    file_path.write_text(content, encoding="utf-8")

    return file_path, tags