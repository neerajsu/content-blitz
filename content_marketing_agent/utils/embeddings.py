"""Embedding utilities with sane defaults and fallbacks."""

from __future__ import annotations

import os
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

# Avoid importing torch-heavy deps unless explicitly requested
HF_ENABLED = os.getenv("USE_HF_EMBEDDINGS", "false").lower() in {"1", "true", "yes"}
if HF_ENABLED:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except Exception:  # pragma: no cover - optional dependency
        HuggingFaceEmbeddings = None  # type: ignore
else:
    HuggingFaceEmbeddings = None  # type: ignore


def get_embeddings(model_name: Optional[str] = None) -> Embeddings:
    """
    Return an embeddings model, preferring OpenAI when configured.

    Args:
        model_name: Optional model override.

    Returns:
        Embeddings implementation.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return OpenAIEmbeddings(model=model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))

    if HF_ENABLED and HuggingFaceEmbeddings:
        return HuggingFaceEmbeddings(model_name=model_name or "sentence-transformers/all-MiniLM-L6-v2")

    try:
        from langchain_community.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=384)
    except Exception as exc:  # pragma: no cover - fallback path
        raise RuntimeError(
            "No embeddings provider configured. Set OPENAI_API_KEY or install sentence-transformers."
        ) from exc
