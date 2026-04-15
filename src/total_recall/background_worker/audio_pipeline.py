from __future__ import annotations

import logging
from pathlib import Path

from total_recall.background_worker.file_utils import compress_for_asr_tempdir
from total_recall.background_worker.system_prompts import get_normalize_to_markdown
from total_recall.background_worker.write_markdown import process_json_response
from total_recall.models import JobResult
from total_recall.rag_core.llm_client import OpenAICompatibleClient
from total_recall.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_audio_to_markdown(
    source_audio: Path,
    output_md: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
    transcription_model: str,
) -> JobResult:
    try:
        LOG.info("Starting audio pipeline source=%s transcription_model=%s", source_audio, transcription_model)
        vault_root = output_md if output_md.is_dir() else output_md.parent
        source_audio = compress_for_asr_tempdir(source_audio)
        LOG.debug("Prepared audio source path=%s", source_audio)
        transcript = llm_client.transcribe_audio(source_audio, transcription_model)
        LOG.info("Completed audio transcription source=%s transcript_chars=%s", source_audio, len(transcript))

        tags = tag_catalog.store.get_tags()
        dir_structure = ",".join(str(p.relative_to(vault_root)) for p in vault_root.rglob("*") if p.is_dir())
        LOG.debug("Normalizing audio markdown source=%s known_tag_count=%s", source_audio, len(tags))
        prompt = get_normalize_to_markdown(", ".join(tags), transcript, dir_structure, source_audio)
        json_response = llm_client.chat(prompt)

        output_md, tags = process_json_response(json_response, vault_root)
        tag_catalog.persist_doc_tags(str(output_md), tags)
        LOG.info("Completed audio pipeline source=%s output_doc=%s tag_count=%s", source_audio, output_md, len(tags))
        return JobResult(source_path=source_audio, success=True, message="audio processed", output_doc=output_md)
    except Exception as exc:
        LOG.exception("Audio pipeline failed source=%s", source_audio)
        return JobResult(source_path=source_audio, success=False, message=str(exc))
