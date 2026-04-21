from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Sequence

import requests

from app.utils.logging_config import get_logger
from configs.ai_config import load_ai_config


class VectorService:
    """Service for converting text/keywords into vectors for similarity search."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.vector_service")
        self.ai_config = load_ai_config()
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    @staticmethod
    def _normalize_vector(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return vector
        return [x / norm for x in vector]

    @staticmethod
    def _weighted_average(vectors: list[list[float]], weights: list[float]) -> list[float]:
        if not vectors:
            return []
        if len(vectors) != len(weights):
            raise ValueError("vectors and weights length mismatch")

        dim = len(vectors[0])
        agg = [0.0] * dim
        total = sum(weights)
        if total <= 0:
            total = float(len(weights))
            weights = [1.0] * len(weights)

        for vec, weight in zip(vectors, weights):
            if len(vec) != dim:
                raise ValueError("all vectors must have the same dimension")
            for idx, value in enumerate(vec):
                agg[idx] += value * weight

        return [value / total for value in agg]

    @staticmethod
    def _split_text(text: str, chunk_size: int = 1200, overlap: int = 120) -> list[str]:
        content = re.sub(r"\s+", " ", text or "").strip()
        if not content:
            return []

        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and < chunk_size")

        chunks: list[str] = []
        start = 0
        step = chunk_size - overlap
        length = len(content)

        while start < length:
            end = min(start + chunk_size, length)
            chunks.append(content[start:end])
            if end >= length:
                break
            start += step

        return chunks

    def _fallback_hash_embedding(self, text: str, dim: int = 384) -> list[float]:
        """
        Deterministic fallback embedding:
        convert tokens to signed hashed buckets and L2 normalize.
        """
        tokens = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]+", text.lower())
        if not tokens:
            return [0.0] * dim

        vec = [0.0] * dim
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], byteorder="big") % dim
            sign = 1.0 if (digest[4] & 1) == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vec[idx] += sign * weight

        return self._normalize_vector(vec)

    def _embed_batch(self, inputs: Sequence[str]) -> list[list[float]]:
        cleaned = [item.strip() for item in inputs if item and item.strip()]
        if not cleaned:
            return []

        if not self.ai_config.api_key:
            self.logger.warning("AI_API_KEY missing, using fallback hash embedding.")
            return [self._fallback_hash_embedding(item) for item in cleaned]

        url = f"{self.ai_config.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.ai_config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.embedding_model,
            "input": cleaned,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.ai_config.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("data", [])
            vectors = [item.get("embedding", []) for item in items]
            if len(vectors) != len(cleaned) or any(not vec for vec in vectors):
                raise RuntimeError(f"Invalid embedding response: {data}")
            return [[float(v) for v in vec] for vec in vectors]
        except Exception:
            self.logger.exception("Embedding request failed, using fallback hash embedding.")
            return [self._fallback_hash_embedding(item) for item in cleaned]

    def embed_long_text(
        self,
        text: str,
        chunk_size: int = 1200,
        overlap: int = 120,
    ) -> list[float]:
        """
        Convert long text to a retrieval-ready vector.
        Strategy: split into chunks -> embed per chunk -> length-weighted merge.
        """
        chunks = self._split_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return []

        vectors = self._embed_batch(chunks)
        weights = [float(len(chunk)) for chunk in chunks]
        merged = self._weighted_average(vectors, weights)
        return self._normalize_vector(merged)

    def embed_keywords(self, keywords: Sequence[str]) -> list[float]:
        """
        Convert keywords into a retrieval-ready vector.
        Strategy:
        1) embed a keyword sentence to keep global semantics
        2) embed each keyword and mean-pool to keep token-level signal
        3) mix with fixed ratio: 0.6 * sentence + 0.4 * mean(keyword vectors)
        """
        cleaned = []
        seen = set()
        for keyword in keywords:
            token = (keyword or "").strip()
            if not token:
                continue
            lower = token.lower()
            if lower in seen:
                continue
            seen.add(lower)
            cleaned.append(token)

        if not cleaned:
            return []

        keyword_sentence = "Keywords for semantic retrieval: " + ", ".join(cleaned)
        vectors = self._embed_batch([keyword_sentence] + cleaned)
        sentence_vector = vectors[0]
        term_vectors = vectors[1:] if len(vectors) > 1 else [sentence_vector]

        term_mean = self._weighted_average(term_vectors, [1.0] * len(term_vectors))
        mixed = [
            (0.6 * sent_val) + (0.4 * term_val)
            for sent_val, term_val in zip(sentence_vector, term_mean)
        ]
        return self._normalize_vector(mixed)
