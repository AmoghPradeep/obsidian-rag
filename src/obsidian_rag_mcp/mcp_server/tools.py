from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from obsidian_rag_mcp.background_worker.write_markdown import resolve_safe_output_dir
from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.rag_core.embeddings import EmbeddingService
from obsidian_rag_mcp.rag_core.indexing import index_markdown_document
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.manifest import VaultManifest, compute_vault_fingerprints
from obsidian_rag_mcp.rag_core.retrieval import RetrievalService
from obsidian_rag_mcp.rag_core.vector_store.sqlite_store import SQLiteVectorStore


@dataclass(slots=True)
class ReindexResult:
    processed: int
    skipped: int
    deleted: int
    errors: int


class MCPTools:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = SQLiteVectorStore(config.db_path)
        self.embeddings = EmbeddingService(config.models.llm_service_url, config.models.embedding_model)
        self.manifest = VaultManifest(config.manifest_path)
        self.retrieval = RetrievalService(self.embeddings, self.store)
        self.llm_client = OpenAICompatibleClient(config.models.llm_service_url, config.models.generation_model)

    def reindex_vault_delta(self) -> dict:
        previous = self.manifest.load()
        current = compute_vault_fingerprints(self.config.vault_path)

        prev_paths = set(previous)
        curr_paths = set(current)

        deleted = prev_paths - curr_paths
        new_or_changed = {p for p in curr_paths if previous.get(p) != current[p]}

        metrics = ReindexResult(processed=0, skipped=0, deleted=0, errors=0)

        for path in sorted(deleted):
            self.store.delete_by_doc(path)
            metrics.deleted += 1

        for path in sorted(new_or_changed):
            try:
                md_path = Path(path)
                content = md_path.read_text(encoding="utf-8")
                count = index_markdown_document(
                    md_path,
                    content,
                    self.embeddings,
                    self.store,
                    chunk_size=self.config.chunking.chunk_size,
                    chunk_overlap=self.config.chunking.chunk_overlap,
                )
                if count > 0:
                    metrics.processed += 1
                else:
                    metrics.skipped += 1
            except Exception:
                metrics.errors += 1

        for path in sorted(curr_paths - new_or_changed):
            metrics.skipped += 1

        self.manifest.save(current)
        return asdict(metrics)

    def query_vault_context(self, query: str, k: int = 5) -> dict:
        results = self.retrieval.query(query, k)
        normalized = []
        for row in results:
            normalized.append(
                {
                    "chunk_id": row["chunk_id"],
                    "content": row["content"],
                    "doc_path": row["doc_path"],
                    "score": float(row["score"]),
                    "source": {"doc_path": row["doc_path"], "chunk_id": row["chunk_id"]},
                    "similarity_score": float(row["score"]),
                }
            )
        return {"k": len(normalized), "results": normalized}

    def update_markdown_note(self, note_reference: str, update_context: str = "", confidence_threshold: float = 0.65) -> dict:
        candidates = self._fuzzy_candidates(note_reference)
        if not candidates:
            return {
                "status": "not_found",
                "note_reference": note_reference,
                "confidence": 0.0,
                "confidence_threshold": confidence_threshold,
                "candidates": [],
                "changes_applied": False,
            }

        resolution = self._resolve_candidate_with_llm(note_reference, candidates, update_context)
        confidence = float(resolution.get("confidence", 0.0))
        target_path = Path(resolution.get("selected_path", ""))

        if confidence < confidence_threshold or not target_path.exists():
            return {
                "status": "ambiguous",
                "note_reference": note_reference,
                "confidence": confidence,
                "confidence_threshold": confidence_threshold,
                "candidates": candidates,
                "changes_applied": False,
            }

        old_path = target_path
        original_content = old_path.read_text(encoding="utf-8")

        summary = self._generate_summary(original_content, update_context)
        tags = self._generate_tags(original_content, update_context)
        updated = self._upsert_managed_sections(original_content, summary, tags)
        old_path.write_text(updated, encoding="utf-8")

        recommended_rel = self._recommend_relative_path(old_path, note_reference, update_context)
        safe_dir, used_fallback = resolve_safe_output_dir(self.config.vault_path, recommended_rel)
        new_path = self._move_if_needed(old_path, safe_dir)

        if str(new_path) != str(old_path):
            self.store.delete_by_doc(str(old_path))

        indexed_chunks = index_markdown_document(
            new_path,
            new_path.read_text(encoding="utf-8"),
            self.embeddings,
            self.store,
            chunk_size=self.config.chunking.chunk_size,
            chunk_overlap=self.config.chunking.chunk_overlap,
        )

        return {
            "status": "updated",
            "note_reference": note_reference,
            "confidence": confidence,
            "confidence_threshold": confidence_threshold,
            "resolved_file": str(new_path),
            "old_path": str(old_path),
            "new_path": str(new_path),
            "moved": str(new_path) != str(old_path),
            "path_fallback_used": used_fallback,
            "summary_updated": True,
            "tags_updated": True,
            "changes_applied": True,
            "indexed_chunks": indexed_chunks,
            "candidate_count": len(candidates),
        }

    def _fuzzy_candidates(self, note_reference: str, limit: int = 8) -> list[dict]:
        ref = note_reference.strip().lower()
        files = sorted(self.config.vault_path.rglob("*.md"))
        scored: list[dict] = []
        for file in files:
            name = file.stem.lower()
            rel = str(file.relative_to(self.config.vault_path)).lower()
            score = max(
                SequenceMatcher(a=ref, b=name).ratio(),
                SequenceMatcher(a=ref, b=rel).ratio(),
            )
            if ref in name or ref in rel:
                score = max(score, 0.95)
            scored.append({"path": str(file), "score": round(score, 4)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return [row for row in scored[:limit] if row["score"] > 0.15]

    def _resolve_candidate_with_llm(self, note_reference: str, candidates: list[dict], update_context: str) -> dict:
        if len(candidates) == 1:
            return {"selected_path": candidates[0]["path"], "confidence": candidates[0]["score"]}

        listed = "\n".join(f"- {c['path']} (score={c['score']})" for c in candidates)
        prompt = f"""
Pick the best markdown file for this user note reference.
Return STRICT JSON: {{"selected_path":"...","confidence":0.0}}
If ambiguous, return confidence below 0.65.

Reference: {note_reference}
Update context: {update_context}
Candidates:
{listed}
"""
        raw = self.llm_client.chat(prompt, generation_mode="openai", allow_local_fallback=True, require_success=False)
        try:
            parsed = json.loads(_strip_fence(raw))
            selected = str(parsed.get("selected_path", "")).strip()
            confidence = float(parsed.get("confidence", 0.0))
            if selected:
                return {"selected_path": selected, "confidence": confidence}
        except Exception:
            pass

        # deterministic lexical fallback
        top = candidates[0]
        return {"selected_path": top["path"], "confidence": min(float(top["score"]), 0.64)}

    def _generate_summary(self, content: str, update_context: str) -> str:
        prompt = f"""
Summarize this markdown note in 5-8 concise bullet points.
No markdown title. Only bullet list.
Context: {update_context}

NOTE:
{content[:16000]}
"""
        return self.llm_client.chat(prompt, generation_mode="openai", allow_local_fallback=True, require_success=True).strip()

    def _generate_tags(self, content: str, update_context: str) -> list[str]:
        prompt = f"""
Return up to 8 broad knowledge-domain tags as comma-separated values.
No hash prefix. Lowercase.
Context: {update_context}

NOTE:
{content[:12000]}
"""
        raw = self.llm_client.chat(prompt, generation_mode="openai", allow_local_fallback=True, require_success=True)
        tags = [t.strip().lower().replace(" ", "-") for t in raw.split(",") if t.strip()]
        return sorted(set(tags))[:8]

    def _upsert_managed_sections(self, content: str, summary: str, tags: list[str]) -> str:
        updated = _upsert_h2_section(content, "Summary", summary)
        updated = _upsert_h2_section(updated, "Tags", "\n".join(f"- {t}" for t in tags))
        return updated

    def _recommend_relative_path(self, file_path: Path, note_reference: str, update_context: str) -> str:
        dirs = sorted({str(p.relative_to(self.config.vault_path)).replace("\\", "/") for p in self.config.vault_path.rglob("*") if p.is_dir()})
        dirs_list = ", ".join(dirs[:300])
        current_rel = str(file_path.parent.relative_to(self.config.vault_path)).replace("\\", "/")
        prompt = f"""
Select the best vault-relative directory for this markdown note.
Return ONLY the relative directory path.
Never return absolute paths.
If unsure, return current directory.

Current directory: {current_rel}
Note reference: {note_reference}
Update context: {update_context}
Existing directories: {dirs_list}
"""
        raw = self.llm_client.chat(prompt, generation_mode="openai", allow_local_fallback=True, require_success=False).strip()
        cleaned = raw.splitlines()[0].strip() if raw else current_rel
        return cleaned or current_rel

    def _move_if_needed(self, old_path: Path, target_dir: Path) -> Path:
        if old_path.parent.resolve() == target_dir.resolve():
            return old_path

        target_dir.mkdir(parents=True, exist_ok=True)
        destination = target_dir / old_path.name
        if destination.resolve() == old_path.resolve():
            return old_path

        counter = 1
        stem = old_path.stem
        suffix = old_path.suffix
        while destination.exists():
            destination = target_dir / f"{stem} {counter}{suffix}"
            counter += 1

        shutil.move(str(old_path), str(destination))
        return destination


def _upsert_h2_section(content: str, section_title: str, section_body: str) -> str:
    body = section_body.strip() or "- (none)"
    replacement = f"## {section_title}\n{body}\n"
    pattern = re.compile(rf"(?ms)^## {re.escape(section_title)}\n.*?(?=^## |\Z)")
    if pattern.search(content):
        return pattern.sub(replacement, content).rstrip() + "\n"
    return content.rstrip() + "\n\n" + replacement


def _strip_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()
