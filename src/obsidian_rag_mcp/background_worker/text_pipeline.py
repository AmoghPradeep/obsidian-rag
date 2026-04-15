from __future__ import annotations

import logging
from pathlib import Path

from obsidian_rag_mcp.background_worker.system_prompts import get_normalize_text_to_markdown
from obsidian_rag_mcp.background_worker.write_markdown import process_json_response
from obsidian_rag_mcp.models import JobResult
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_text_to_markdown(
    source_text: Path,
    output_md: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    try:
        LOG.info("Starting text pipeline source=%s", source_text)
        vault_root = output_md if output_md.is_dir() else output_md.parent
        raw_content = source_text.read_text(encoding="utf-8")
        LOG.info("Loaded text source source=%s char_count=%s", source_text, len(raw_content))

        tags = tag_catalog.store.get_tags()
        dir_structure = ",".join(str(p.relative_to(vault_root)) for p in vault_root.rglob("*") if p.is_dir())
        LOG.debug("Normalizing text markdown source=%s known_tag_count=%s", source_text, len(tags))
        prompt = get_normalize_text_to_markdown(", ".join(tags), raw_content, dir_structure, source_text)
        json_response = llm_client.chat(prompt)

        output_md, tags = process_json_response(json_response, vault_root)
        tag_catalog.persist_doc_tags(str(output_md), tags)
        LOG.info("Completed text pipeline source=%s output_doc=%s tag_count=%s", source_text, output_md, len(tags))
        return JobResult(source_path=source_text, success=True, message="text processed", output_doc=output_md)
    except Exception as exc:
        LOG.exception("Text pipeline failed source=%s", source_text)
        return JobResult(source_path=source_text, success=False, message=str(exc))
