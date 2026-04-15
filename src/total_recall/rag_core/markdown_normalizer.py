from __future__ import annotations

import hashlib
from datetime import datetime, UTC

import yaml


def normalize_markdown(content: str, source: str, summary: str, tags: list[str]) -> str:
    payload = {
        "source": source,
        "created_at": datetime.now(UTC).isoformat(),
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "tags": tags,
    }
    frontmatter = yaml.safe_dump(payload, sort_keys=False).strip()
    normalized = [
        "---",
        frontmatter,
        "---",
        "",
        "# Summary",
        summary.strip(),
        "",
        "# Content",
        content.strip(),
        "",
    ]
    return "\n".join(normalized)
