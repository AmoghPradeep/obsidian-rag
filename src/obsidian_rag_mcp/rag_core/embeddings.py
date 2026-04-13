from __future__ import annotations

import hashlib
import random
import time
from typing import Iterable
from openai import OpenAI

import httpx


class EmbeddingService:
    def __init__(self, base_url: str, model: str, retries: int = 2, backoff_seconds: float = 0.5, batch_size: int = 16) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.batch_size = batch_size

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors.extend(self._embed_batch_with_retry(batch))
        return vectors

    def _embed_batch_with_retry(self, batch: list[str]) -> list[list[float]]:
        attempt = 0
        while True:
            try:
                client = OpenAI()

                response = client.embeddings.create(
                    input= batch,
                    model=self.model
                )

                embeddings: list[list[float]] = [
                    item.embedding
                    for item in sorted(response.data, key=lambda x: x.index)
                ]
                return embeddings

            except Exception:
                pass

            if attempt >= self.retries:
                return [self._hash_embedding(text) for text in batch]
            sleep_for = self.backoff_seconds * (2**attempt) + random.uniform(0, 0.2)
            time.sleep(sleep_for)
            attempt += 1

    @staticmethod
    def _hash_embedding(text: str, dims: int = 64) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vals = [b / 255.0 for b in digest]
        out = [vals[i % len(vals)] for i in range(dims)]
        return out
