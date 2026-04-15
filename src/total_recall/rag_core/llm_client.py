from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from openai import OpenAI

LOG = logging.getLogger(__name__)
OPENAI_API_BASE_URL = "https://api.openai.com/v1"


class OpenAICompatibleClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(
        self,
        prompt: str,
        images: list[str] | None = None,
        require_success: bool = False,
    ) -> str:
        try:
            LOG.debug(
                "Submitting generation request model=%s image_count=%s base_url=%s require_success=%s",
                self.model,
                len(images or []),
                self.base_url or OPENAI_API_BASE_URL,
                require_success,
            )
            client = self._client()
            response = client.responses.create(
                model=self.model,
                input=self._build_input(prompt, images),
            )
            LOG.info("Generation request completed model=%s image_count=%s", self.model, len(images or []))
            return response.output_text
        except Exception as exc:
            LOG.error(
                "Generation request failed model=%s image_count=%s require_success=%s error=%s",
                self.model,
                len(images or []),
                require_success,
                exc,
            )
            if require_success:
                raise RuntimeError(f"Generation failed: {exc}") from exc
            return prompt[:2000]

    def transcribe_audio(self, audio_path: Path, model: str) -> str:
        try:
            LOG.debug("Submitting transcription request model=%s source=%s", model, audio_path)
            with audio_path.open("rb") as audio_file:
                client = self._client()
                response = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                )
            LOG.info("Transcription request completed model=%s source=%s", model, audio_path)
            return str(response)
        except Exception as exc:
            LOG.error("Transcription request failed model=%s source=%s error=%s", model, audio_path, exc)
            raise RuntimeError(f"Transcription failed: {exc}") from exc

    def _client(self) -> OpenAI:
        if not self.base_url or self.base_url == OPENAI_API_BASE_URL:
            return OpenAI()
        api_key = os.getenv("OPENAI_API_KEY", "remote-api-key")
        return OpenAI(base_url=self.base_url, api_key=api_key)

    def _build_input(self, prompt: str, images: list[str] | None):
        if not images:
            return prompt

        content: list[dict] = [{"type": "input_text", "text": prompt}]
        for image_path in images:
            url = self._to_data_url(Path(image_path))
            content.append({"type": "input_image", "image_url": url})

        return [{"role": "user", "content": content}]

    @staticmethod
    def _to_data_url(path: Path) -> str:
        mime = "image/jpeg"
        if path.suffix.lower() == ".png":
            mime = "image/png"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
