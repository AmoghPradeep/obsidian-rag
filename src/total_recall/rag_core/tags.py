from __future__ import annotations

from difflib import SequenceMatcher

from total_recall.rag_core.vector_store.sqlite_store import SQLiteVectorStore


class TagCatalog:
    def __init__(self, store: SQLiteVectorStore, threshold: float = 0.72) -> None:
        self.store = store
        self.threshold = threshold

    def suggest_reusable(self, candidates: list[str]) -> tuple[list[str], list[str]]:
        existing = self.store.get_tags()
        reusable: list[str] = []
        new_tags: list[str] = []
        for candidate in candidates:
            match = self._best_match(candidate, existing)
            if match:
                reusable.append(match)
            else:
                new_tags.append(candidate)
        return sorted(set(reusable)), sorted(set(new_tags))

    def persist_doc_tags(self, doc_path: str, tags: list[str]) -> None:
        normalized = [t.strip().lower().replace(" ", "-") for t in tags if t.strip()]
        self.store.upsert_doc_tags(doc_path, sorted(set(normalized)))

    def _best_match(self, candidate: str, existing: list[str]) -> str | None:
        best_tag: str | None = None
        best_score = 0.0
        for tag in existing:
            score = SequenceMatcher(a=candidate.lower(), b=tag.lower()).ratio()
            if score > best_score:
                best_score = score
                best_tag = tag
        if best_score >= self.threshold:
            return best_tag
        return None
