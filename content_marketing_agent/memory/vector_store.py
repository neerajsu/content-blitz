"""FAISS-backed vector store manager for long-term memory collections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

COLLECTIONS = {"brand_voice", "past_outputs", "research_cache"}


class VectorStoreManager:
    """Manages multiple FAISS collections with shared embedding model."""

    def __init__(self, embeddings: Embeddings, base_path: str = "content_marketing_agent/vector_data") -> None:
        self.embeddings = embeddings
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.stores: Dict[str, FAISS] = {}

    def _collection_path(self, collection: str) -> Path:
        return self.base_path / collection

    def load_existing(self, collection: str) -> FAISS | None:
        """Load an existing collection if present."""
        if collection not in COLLECTIONS:
            raise ValueError(f"Unsupported collection: {collection}")

        if collection in self.stores:
            return self.stores[collection]

        path = self._collection_path(collection)
        if path.exists():
            store = FAISS.load_local(str(path), self.embeddings, allow_dangerous_deserialization=True)
            self.stores[collection] = store
            return store
        return None

    def add_document(self, collection: str, content: str, metadata: Dict[str, str]) -> None:
        """Add a document to the specified collection."""
        doc = Document(page_content=content, metadata=metadata)

        store = self.load_existing(collection)
        if store is None:
            # Create a new store with the first document to avoid empty FAISS creation
            store = FAISS.from_documents([doc], self.embeddings)
            self.stores[collection] = store
        else:
            store.add_documents([doc])

        path = self._collection_path(collection)
        path.mkdir(parents=True, exist_ok=True)
        store.save_local(str(path))

    def search(self, collection: str, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        """Search for similar documents in a collection."""
        store = self.load_existing(collection)
        if store is None:
            return []
        docs = store.similarity_search_with_score(query, k=k)
        return docs

    def as_json(self, docs: List[Tuple[Document, float]]) -> List[Dict[str, str]]:
        """Convert documents to a JSON-serializable list."""
        payload: List[Dict[str, str]] = []
        for doc, score in docs:
            payload.append({"content": doc.page_content, "metadata": json.dumps(doc.metadata), "score": f"{score:.4f}"})
        return payload
