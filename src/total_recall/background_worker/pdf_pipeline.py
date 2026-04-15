from __future__ import annotations

import logging
import shutil
from pathlib import Path
from uuid import uuid4
from PIL import Image

try:
    import pypdfium2 as pdfium
except Exception:  # pragma: no cover
    pdfium = None

from total_recall.background_worker.page_document_pipeline import build_vault_backlink, process_page_images_to_markdown
from total_recall.models import JobResult
from total_recall.rag_core.llm_client import OpenAICompatibleClient
from total_recall.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)

PDF_IMAGE_MAX_LONG_EDGE = 1800
PDF_IMAGE_QUALITY = 78


def process_pdf_to_markdown(
    source_pdf: Path,
    output_md: Path,
    image_dir: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    temp_job_dir = image_dir / f"pdf-pages-{uuid4().hex}"

    try:
        LOG.info("Starting PDF pipeline source=%s temp_dir=%s", source_pdf, temp_job_dir)
        page_images = convert_pdf_to_jpg_pages(source_pdf, temp_job_dir)
        LOG.info("Rendered PDF pages source=%s page_count=%s", source_pdf, len(page_images))
        vault_root = output_md if output_md.is_dir() else output_md.parent
        result = process_page_images_to_markdown(
            source_path=source_pdf,
            page_images=page_images,
            output_md=output_md,
            llm_client=llm_client,
            tag_catalog=tag_catalog,
            source_backlinks=[build_vault_backlink(vault_root, source_pdf)],
        )
        LOG.info("Completed PDF pipeline source=%s success=%s output_doc=%s", source_pdf, result.success, result.output_doc)
        return result
    except Exception as exc:
        LOG.exception("PDF pipeline failed source=%s", source_pdf)
        return JobResult(source_path=source_pdf, success=False, message=str(exc))
    finally:
        shutil.rmtree(temp_job_dir, ignore_errors=True)
        LOG.debug("Removed temporary PDF image directory path=%s", temp_job_dir)


def convert_pdf_to_jpg_pages(pdf_path: Path, image_dir: Path) -> list[Path]:
    if pdfium is None:
        raise RuntimeError("pypdfium2 is not installed; cannot render PDF pages")

    image_dir.mkdir(parents=True, exist_ok=True)
    LOG.debug("Rendering PDF pages source=%s output_dir=%s", pdf_path, image_dir)
    pdf = pdfium.PdfDocument(str(pdf_path))
    pages: list[Path] = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil().convert("L")
        pil_image = _resize_preserving_long_edge(pil_image, PDF_IMAGE_MAX_LONG_EDGE)

        out = image_dir / f"{pdf_path.stem}-page-{i+1}.jpg"
        pil_image.save(out, format="JPEG", quality=PDF_IMAGE_QUALITY, optimize=True, progressive=True)
        pages.append(out)
    LOG.debug("Finished rendering PDF pages source=%s page_count=%s", pdf_path, len(pages))
    return pages


def _resize_preserving_long_edge(image, max_long_edge: int):
    width, height = image.size
    long_edge = max(width, height)
    if long_edge <= max_long_edge:
        return image
    scale = max_long_edge / float(long_edge)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, resample=Image.LANCZOS)
