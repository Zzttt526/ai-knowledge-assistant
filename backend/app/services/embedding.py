"""Embedding provider with lazy sentence-transformers initialization."""

from __future__ import annotations

import hashlib
import math
from typing import Sequence


class EmbeddingService:
    def __init__(self, model_name: str, allow_fallback: bool = True) -> None:
        self.model_name = model_name
        self.allow_fallback = allow_fallback
        self._model = None
        self._load_attempted = False

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        if model is None:
            return [self._fallback_embedding(text) for text in texts]
        vectors = model.encode(list(texts), normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def _get_model(self):
        if self._load_attempted:
            return self._model
        self._load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        except Exception:
            if not self.allow_fallback:
                raise RuntimeError("无法加载 embedding 模型，请检查 MODEL_NAME 与模型依赖")
        return self._model

    @staticmethod
    def _fallback_embedding(text: str, dimensions: int = 384) -> list[float]:
        """Deterministic development fallback; never use it for production retrieval."""
        values: list[float] = []
        seed = text.encode("utf-8")
        while len(values) < dimensions:
            seed = hashlib.sha256(seed).digest()
            values.extend((byte / 127.5) - 1.0 for byte in seed)
        vector = values[:dimensions]
        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]
