from __future__ import annotations

import gc
import logging
import time
from pathlib import Path
from typing import Optional, Union

import httpx

try:
    import torch
    from transformers import AutoProcessor, CohereAsrForConditionalGeneration
    from transformers.audio_utils import load_audio
except ImportError:  # pragma: no cover - optional runtime dependency
    torch = None
    AutoProcessor = None
    CohereAsrForConditionalGeneration = None
    load_audio = None

LOG = logging.getLogger(__name__)


class LLMRuntimeManager:
    def __init__(self, service_url: str, model_name: str) -> None:
        self.service_url = service_url.rstrip("/")
        self.model_name = model_name
        self.local_model_loaded = False

    def service_is_healthy(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.service_url}/v1/models")
            return resp.status_code < 400
        except Exception:
            return False

    def ensure_generation_mode(self) -> str:
        return "openai"

    def load_local_model(self) -> None:
        if self.local_model_loaded:
            return
        LOG.info("Loading local LLM model %s", self.model_name)
        time.sleep(0.05)
        self.local_model_loaded = True

    def eject_local_model(self) -> None:
        if not self.local_model_loaded:
            return
        LOG.info("Ejecting local LLM model %s", self.model_name)
        self.local_model_loaded = False


class ASRRuntimeManager:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.loaded = False
        self.processor: Optional[object] = None
        self.model: Optional[object] = None

    def load(self) -> None:
        if self.loaded:
            return
        if AutoProcessor is None or CohereAsrForConditionalGeneration is None:
            raise RuntimeError("transformers runtime dependencies are not installed")

        local_path = Path(__file__).resolve().parents[3] / "models" / "cohere-transcribe-03-2026"

        self.processor = AutoProcessor.from_pretrained(
            str(local_path),
            local_files_only=True,
        )

        self.model = CohereAsrForConditionalGeneration.from_pretrained(
            str(local_path),
            device_map="auto",
            local_files_only=True,
        )

        self.loaded = True

    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: str = "en",
        sampling_rate: int = 16000,
        max_new_tokens: int = 256,
    ) -> str:
        if not self.loaded or self.processor is None or self.model is None:
            raise RuntimeError("Model is not loaded. Call load() first.")
        if load_audio is None:
            raise RuntimeError("transformers runtime dependencies are not installed")

        audio = load_audio(str(audio_path), sampling_rate=sampling_rate)

        inputs = self.processor(
            audio,
            sampling_rate=sampling_rate,
            return_tensors="pt",
            language=language,
        )

        inputs.to(self.model.device, dtype=self.model.dtype)

        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        text = self.processor.decode(outputs, skip_special_tokens=True)

        return " ".join(text)

    def eject(self) -> None:
        if self.model is not None:
            del self.model
        if self.processor is not None:
            del self.processor

        self.model = None
        self.processor = None
        self.loaded = False

        gc.collect()

        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()
