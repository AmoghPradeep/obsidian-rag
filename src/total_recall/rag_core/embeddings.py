from __future__ import annotations

import hashlib
import logging
import os
import random
import time
from openai import OpenAI

LOG = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, base_url: str, model: str, retries: int = 2, backoff_seconds: float = 0.5, batch_size: int = 16) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.batch_size = batch_size

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        LOG.debug("Embedding text batch total_texts=%s batch_size=%s model=%s", len(texts), self.batch_size, self.model)
        vectors: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors.extend(self._embed_batch_with_retry(batch))
        return vectors

    def _embed_batch_with_retry(self, batch: list[str]) -> list[list[float]]:
        attempt = 0
        while True:
            try:
                LOG.debug("Submitting embedding batch model=%s batch_size=%s attempt=%s", self.model, len(batch), attempt + 1)
                client = self._client()

                response = client.embeddings.create(
                    input=batch,
                    model=self.model,
                )

                embeddings: list[list[float]] = [
                    item.embedding
                    for item in sorted(response.data, key=lambda x: x.index)
                ]
                LOG.info("Embedding batch completed model=%s batch_size=%s", self.model, len(batch))
                return embeddings

            except Exception as exc:
                if attempt >= self.retries:
                    LOG.error(
                        "Embedding batch failed after retries model=%s batch_size=%s attempts=%s error=%s",
                        self.model,
                        len(batch),
                        attempt + 1,
                        exc,
                    )
                    return [self._hash_embedding(text) for text in batch]
                LOG.warning(
                    "Embedding batch failed, retrying model=%s batch_size=%s attempt=%s error=%s",
                    self.model,
                    len(batch),
                    attempt + 1,
                    exc,
                )
            sleep_for = self.backoff_seconds * (2**attempt) + random.uniform(0, 0.2)
            time.sleep(sleep_for)
            attempt += 1

    def _client(self) -> OpenAI:
        if not self.base_url or self.base_url == "https://api.openai.com/v1":
            return OpenAI()
        api_key = os.getenv("OPENAI_API_KEY", "remote-api-key")
        return OpenAI(base_url=self.base_url, api_key=api_key)

    @staticmethod
    def _hash_embedding(text: str, dims: int = 64) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vals = [b / 255.0 for b in digest]
        out = [vals[i % len(vals)] for i in range(dims)]
        return out
