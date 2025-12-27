"""Vector store helpers backed by Pinecone (local or hosted)."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Iterable, List

from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from content_marketing_agent.utils.embedding_loader import get_embedding_dimension, get_embedding_model

logger = logging.getLogger(__name__)

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "content-blitz")
DEFAULT_METRIC = os.getenv("PINECONE_METRIC", "cosine")


def _list_index_names(client: Pinecone) -> set[str]:
    try:
        indexes = client.list_indexes()
        if hasattr(indexes, "names"):
            return set(indexes.names())
        if isinstance(indexes, dict) and "indexes" in indexes:
            return {idx.get("name", "") for idx in indexes["indexes"] if idx.get("name")}
        return {getattr(idx, "name", str(idx)) for idx in indexes}
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not list Pinecone indexes: %s", exc)
        return set()


@lru_cache(maxsize=1)
def _embedding():
    return get_embedding_model()


@lru_cache(maxsize=1)
def _pinecone_client() -> Pinecone:
    api_key = os.getenv("PINECONE_API_KEY", "local-dev-key")
    host = os.getenv("PINECONE_HOST")
    if host:
        logger.info("Using Pinecone local host: %s", host)
        return Pinecone(api_key=api_key, host=host)
    logger.info("Using Pinecone client with default environment")
    return Pinecone(api_key=api_key)


def _ensure_index(dimension: int) -> None:
    client = _pinecone_client()
    existing = _list_index_names(client)
    if INDEX_NAME in existing:
        return
    spec = None
    if not os.getenv("PINECONE_HOST"):
        spec = ServerlessSpec(
            cloud=os.getenv("PINECONE_CLOUD", "aws"),
            region=os.getenv("PINECONE_REGION", "us-east-1"),
        )
    logger.info("Creating Pinecone index '%s' (dim=%s)", INDEX_NAME, dimension)
    client.create_index(name=INDEX_NAME, dimension=dimension, metric=DEFAULT_METRIC, spec=spec)


@lru_cache(maxsize=16)
def _vector_store(namespace: str) -> PineconeVectorStore | None:
    """Return a vector store bound to a namespace."""
    try:
        embedding = _embedding()
        dimension = get_embedding_dimension(embedding)
        _ensure_index(dimension)
        client = _pinecone_client()
        host = os.getenv("PINECONE_HOST")
        if host is None:
            raise RuntimeError("PINECONE_HOST environment variable is not set")
        index = client.Index(INDEX_NAME, host=host)
        return PineconeVectorStore(
            index=index,
            embedding=embedding,
            namespace=namespace,
            text_key="text",
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Vector store unavailable for namespace %s: %s", namespace, exc)
        return None


def _build_payload(summary: str, keywords: Iterable[str], insights: Iterable[str]) -> str:
    parts: List[str] = []
    if summary:
        parts.append(summary)
    if keywords:
        parts.append("Keywords: " + ", ".join([kw.strip() for kw in keywords if kw]))
    if insights:
        parts.append("Insights: " + " | ".join([ins.strip() for ins in insights if ins]))
    return "\n".join(parts).strip()


def upsert_research_output(project_id: str, chat_id: str, summary: str, keywords: Any, insights: Any) -> None:
    """Upsert a research output into the Pinecone namespace for a project."""
    namespace = str(project_id)
    payload_text = _build_payload(summary, keywords or [], insights or [])
    if not payload_text:
        logger.info("Skipping vector upsert: no payload text for chat_id=%s", chat_id)
        return

    store = _vector_store(namespace)
    if not store:
        logger.info("Skipping vector upsert: vector store unavailable for namespace %s", namespace)
        return

    metadata = {"chat_id": chat_id, "project_id": project_id}
    logger.info("Upserting research output into vector store (namespace=%s, chat_id=%s)", namespace, chat_id)
    store.add_texts([payload_text], metadatas=[metadata], ids=[chat_id])


def query_project_documents(project_id: str, query: str, k: int = 8) -> list[Document]:
    """Retrieve similar documents for a project namespace."""
    namespace = str(project_id)
    store = _vector_store(namespace)
    if not store:
        logger.info("Vector retrieval skipped: vector store unavailable for namespace %s", namespace)
        return []

    try:
        docs = store.similarity_search(query, k=k)
        logger.info("Retrieved %s vector documents for namespace=%s", len(docs), namespace)
        return docs
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Vector retrieval failed for namespace %s: %s", namespace, exc)
        return []
