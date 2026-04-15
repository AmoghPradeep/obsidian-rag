from __future__ import annotations

import logging
from pathlib import Path

from total_recall.background_worker.page_document_pipeline import build_vault_backlink, process_page_images_to_markdown
from total_recall.background_worker.watchers import list_supported_image_files
from total_recall.models import JobResult
from total_recall.rag_core.llm_client import OpenAICompatibleClient
from total_recall.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_image_folder_to_markdown(
    source_dir: Path,
    output_md: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    try:
        LOG.info("Starting image folder pipeline source=%s", source_dir)
        vault_root = output_md if output_md.is_dir() else output_md.parent
        page_images = list_supported_image_files(source_dir)
        if not page_images:
            LOG.warning("Image folder contains no supported images source=%s", source_dir)
            return JobResult(source_path=source_dir, success=False, message="no supported images in folder", output_doc=None)

        LOG.info("Prepared image folder pipeline source=%s page_count=%s", source_dir, len(page_images))
        backlinks = [build_vault_backlink(vault_root, image) for image in page_images]
        result = process_page_images_to_markdown(
            source_path=source_dir,
            page_images=page_images,
            output_md=output_md,
            llm_client=llm_client,
            tag_catalog=tag_catalog,
            source_backlinks=backlinks,
        )
        LOG.info("Completed image folder pipeline source=%s success=%s output_doc=%s", source_dir, result.success, result.output_doc)
        return result
    except Exception as exc:
        LOG.exception("Image folder pipeline failed source=%s", source_dir)
        return JobResult(source_path=source_dir, success=False, message=str(exc), output_doc=None)
