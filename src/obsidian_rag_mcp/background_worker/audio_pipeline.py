from __future__ import annotations

import logging
from pathlib import Path

from obsidian_rag_mcp.background_worker.llm_runtime import ASRRuntimeManager, LLMRuntimeManager
from obsidian_rag_mcp.models import JobResult
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient, transcribe_audio_fallback
from obsidian_rag_mcp.rag_core.markdown_normalizer import normalize_markdown
from obsidian_rag_mcp.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_audio_to_markdown(
    source_audio: Path,
    output_md: Path,
    asr_runtime: ASRRuntimeManager,
    llm_runtime: LLMRuntimeManager,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    generation_mode = ""
    try:
        asr_runtime.load()
        transcript = asr_runtime.transcribe(source_audio)
        asr_runtime.eject()

        print("transcription:", transcript)

        generation_mode = llm_runtime.ensure_generation_mode()
        tags = _choose_tags(transcript, llm_client, tag_catalog)
        summary = llm_client.chat(f"Summarize this transcript in 3-5 lines:\n\n{transcript}")
        normalized = normalize_markdown(transcript, str(source_audio), summary, tags)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(normalized, encoding="utf-8")
        tag_catalog.persist_doc_tags(str(output_md), tags)
        return JobResult(source_path=source_audio, success=True, message="audio processed", output_doc=output_md)
    except Exception as exc:
        LOG.exception("audio pipeline failed")
        return JobResult(source_path=source_audio, success=False, message=str(exc))
    finally:
        asr_runtime.eject()
        if generation_mode == "local":
            llm_runtime.eject_local_model()


def _choose_tags(content: str, llm_client: OpenAICompatibleClient, tag_catalog: TagCatalog) -> list[str]:
    catalog = tag_catalog.store.get_tags()
    catalog_hint = ", ".join(catalog[:30]) if catalog else "(none)"
    prompt = (
        "Choose up to 5 domain tags for this note. Prefer these existing tags when relevant: "
        f"{catalog_hint}. If no existing tag fits, create minimal new tags. "
        "Return a comma-separated list only.\n\n"
        f"CONTENT:\n{content[:6000]}"
    )
    raw = llm_client.chat(prompt)
    candidates = [x.strip().lower().replace(" ", "-") for x in raw.split(",") if x.strip()]
    reusable, new_tags = tag_catalog.suggest_reusable(candidates)
    tags = sorted(set(reusable + new_tags))
    return tags[:5] if tags else ["general-knowledge"]
