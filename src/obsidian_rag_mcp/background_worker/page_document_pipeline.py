from __future__ import annotations

import re
from pathlib import Path

from obsidian_rag_mcp.background_worker.system_prompts import (
    get_page_document_note_json_prompt,
    get_pdf_page_extract_prompt,
    get_pdf_reduce_prompt,
    get_pdf_tags_prompt,
)
from obsidian_rag_mcp.background_worker.write_markdown import process_json_response
from obsidian_rag_mcp.models import JobResult
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.tags import TagCatalog


def process_page_images_to_markdown(
    source_path: Path,
    page_images: list[Path],
    output_md: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
    source_backlinks: list[str],
) -> JobResult:
    vault_root = output_md if output_md.is_dir() else output_md.parent
    if not page_images:
        return JobResult(source_path=source_path, success=False, message="no page images", output_doc=None)

    page_summaries: list[str] = []
    total_pages = len(page_images)
    for idx, image in enumerate(page_images, start=1):
        page_prompt = get_pdf_page_extract_prompt(idx, total_pages)
        page_summary = llm_client.chat(
            page_prompt,
            images=[str(image)],
            generation_mode="openai",
            allow_local_fallback=True,
            require_success=True,
        )
        page_summaries.append(f"## Page {idx}\n{page_summary}\n")

    full_content = "\n".join(page_summaries)
    reduced_summary = llm_client.chat(
        get_pdf_reduce_prompt(full_content),
        generation_mode="openai",
        allow_local_fallback=True,
        require_success=True,
    )
    tags = _choose_tags(full_content + "\n" + reduced_summary, llm_client, tag_catalog)

    prompt = get_page_document_note_json_prompt(
        ", ".join(tags),
        full_content,
        reduced_summary,
        _dir_structure(vault_root),
        "\n".join(source_backlinks),
    )
    json_response = llm_client.chat(
        prompt,
        generation_mode="openai",
        allow_local_fallback=True,
        require_success=True,
    )

    note_path, parsed_tags = process_json_response(json_response, vault_root)
    _upsert_source_section(note_path, source_backlinks)
    final_tags = parsed_tags if parsed_tags else tags
    tag_catalog.persist_doc_tags(str(note_path), final_tags)
    return JobResult(source_path=source_path, success=True, message="page document processed", output_doc=note_path)


def build_vault_backlink(vault_root: Path, source_path: Path) -> str:
    rel = source_path.resolve().relative_to(vault_root.resolve())
    return f"[[{rel.as_posix()}]]"


def _dir_structure(vault_root: Path) -> str:
    return ",".join(
        str(p.relative_to(vault_root))
        for p in vault_root.rglob("*")
        if p.is_dir() and "z.rawdata" not in str(p)
    )


def _choose_tags(content: str, llm_client: OpenAICompatibleClient, tag_catalog: TagCatalog) -> list[str]:
    catalog = tag_catalog.store.get_tags()
    catalog_hint = ", ".join(catalog[:30]) if catalog else "(none)"
    raw = llm_client.chat(
        get_pdf_tags_prompt(catalog_hint, content[:6000]),
        generation_mode="openai",
        allow_local_fallback=True,
        require_success=True,
    )
    candidates = [x.strip().lower().replace(" ", "-") for x in raw.split(",") if x.strip()]
    reusable, new_tags = tag_catalog.suggest_reusable(candidates)
    tags = sorted(set(reusable + new_tags))
    return tags[:5] if tags else ["general-knowledge"]


def _upsert_source_section(note_path: Path, source_backlinks: list[str]) -> None:
    unique_links = list(dict.fromkeys(link for link in source_backlinks if link))
    if not unique_links:
        return

    body = unique_links[0] if len(unique_links) == 1 else "\n".join(f"- {link}" for link in unique_links)
    replacement = f"## Source\n{body}\n"
    content = note_path.read_text(encoding="utf-8")
    pattern = re.compile(r"(?ms)^## Source\n.*?(?=^## |\Z)")
    if pattern.search(content):
        updated = pattern.sub(replacement, content).rstrip() + "\n"
    else:
        updated = content.rstrip() + "\n\n" + replacement
    note_path.write_text(updated, encoding="utf-8")
