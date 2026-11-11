"""Sentence-transformers embedding model, loaded once and shared (spec §10).

Groq has no embeddings endpoint, so embeddings run locally with a small free model
(all-MiniLM-L6-v2, ~90 MB, downloaded on first use).
"""

import logging
from functools import lru_cache

import numpy as np

logger = logging.getLogger("medbridge.embedder")


class Embedder:
    def __init__(self, model_name: str) -> None:
        # Imported here because loading torch is slow; only pay that cost when needed.
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model %s", model_name)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device="cpu")

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return L2-normalised float32 vectors, so inner product = cosine similarity."""
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype="float32")


@lru_cache
def get_embedder(model_name: str) -> Embedder:
    return Embedder(model_name)
