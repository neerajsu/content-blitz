"""Utility helpers for loading embeddings used by the vector store."""

from __future__ import annotations

import logging
import os
from typing import List

from langchain_core.embeddings import Embeddings

try:
    from langchain_openai import OpenAIEmbeddings
except Exception:  # pragma: no cover - optional dependency
    OpenAIEmbeddings = None  # type: ignore

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except Exception:  # pragma: no cover - optional dependency
    HuggingFaceEmbeddings = None  # type: ignore

logger = logging.getLogger(__name__)


class StubEmbeddings(Embeddings):
    """Embeddings fallback when no provider is configured."""

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self.dimension for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return [0.0] * self.dimension


def get_embedding_model() -> Embeddings:
    """
    Load an embedding model using environment variables.

    Prefers OpenAI embeddings by default; falls back to HuggingFace if requested.
    """
    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    use_hf = os.getenv("USE_HF_EMBEDDINGS", "0") == "1"
    dimension = int(os.getenv("EMBEDDING_DIM", "1536"))

    if use_hf and HuggingFaceEmbeddings:
        logger.info("Loading HuggingFace embeddings: %s", model_name)
        return HuggingFaceEmbeddings(model_name=model_name)

    if OpenAIEmbeddings and os.getenv("OPENAI_API_KEY"):
        logger.info("Loading OpenAI embeddings: %s (dim=%s)", model_name, dimension)
        return OpenAIEmbeddings(model=model_name, dimensions=dimension)

    logger.warning("Falling back to stub embeddings; configure an embedding provider.")
    return StubEmbeddings(dimension=dimension)


def get_embedding_dimension(embedding: Embeddings) -> int:
    """Infer the dimension of an embedding model (with a safe fallback)."""
    try:
        return len(embedding.embed_query("dimension probe"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not infer embedding dimension: %s. Using configured default.", exc)
        return int(os.getenv("EMBEDDING_DIM", "1536"))
