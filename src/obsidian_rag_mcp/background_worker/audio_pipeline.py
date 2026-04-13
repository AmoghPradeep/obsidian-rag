from __future__ import annotations

import logging
import os

from pathlib import Path
from openai import OpenAI
from hashlib import sha256

from obsidian_rag_mcp.background_worker.llm_runtime import ASRRuntimeManager, LLMRuntimeManager
from obsidian_rag_mcp.models import JobResult
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.tags import TagCatalog
from obsidian_rag_mcp.background_worker.system_prompts import get_normalize_to_markdown
from obsidian_rag_mcp.background_worker.write_markdown import process_json_response
from obsidian_rag_mcp.background_worker.file_utils import compress_for_asr_tempdir

LOG = logging.getLogger(__name__)


def process_audio_to_markdown(
    source_audio: Path,
    output_md: Path,
    asr_runtime: ASRRuntimeManager,
    llm_runtime: LLMRuntimeManager,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
    is_last_job: bool = False,
    transcribe_local: bool = False,
) -> JobResult:
    try:
        vault_root = output_md if output_md.is_dir() else output_md.parent
        source_audio = compress_for_asr_tempdir(source_audio)

        if transcribe_local:
            asr_runtime.load()
            transcript = asr_runtime.transcribe(source_audio)
            if is_last_job:
                asr_runtime.eject()

            LOG.info(f"transcription: {transcript}")
        else:
            client = OpenAI()
            audio_file = open(source_audio, "rb")

            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file
            )

            LOG.info(f"transcription: {transcript}")

        generation_mode = llm_runtime.ensure_generation_mode()

        tags = tag_catalog.store.get_tags()

        prompt = get_normalize_to_markdown(", ".join(tags), transcript, ",".join(str(p) for p in vault_root.rglob("*") if p.is_dir()), source_audio)

        json_response = llm_client.chat(prompt, generation_mode = generation_mode)

        output_md, tags = process_json_response(json_response, vault_root)

        tag_catalog.persist_doc_tags(str(output_md), tags)

        return JobResult(source_path=source_audio, success=True, message="audio processed", output_doc=output_md)
    except Exception as exc:
        LOG.exception("audio pipeline failed")
        asr_runtime.eject()
        return JobResult(source_path=source_audio, success=False, message=str(exc))

