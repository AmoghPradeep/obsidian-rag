from __future__ import annotations

import logging
from pathlib import Path

from obsidian_rag_mcp.background_worker.page_document_pipeline import build_vault_backlink, process_page_images_to_markdown
from obsidian_rag_mcp.background_worker.watchers import list_supported_image_files
from obsidian_rag_mcp.models import JobResult
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_image_folder_to_markdown(
    source_dir: Path,
    output_md: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    try:
        vault_root = output_md if output_md.is_dir() else output_md.parent
        page_images = list_supported_image_files(source_dir)
        if not page_images:
            return JobResult(source_path=source_dir, success=False, message="no supported images in folder", output_doc=None)

        backlinks = [build_vault_backlink(vault_root, image) for image in page_images]
        return process_page_images_to_markdown(
            source_path=source_dir,
            page_images=page_images,
            output_md=output_md,
            llm_client=llm_client,
            tag_catalog=tag_catalog,
            source_backlinks=backlinks,
        )
    except Exception as exc:
        LOG.exception("image folder pipeline failed")
        return JobResult(source_path=source_dir, success=False, message=str(exc), output_doc=None)
