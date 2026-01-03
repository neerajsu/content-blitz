"""Shared content state TypedDict to avoid circular imports."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class ContentState(TypedDict, total=False):
    """State container for the content creation flow."""

    project_id: str
    project_title: str
    prompt: str
    history: str
    intent: List[str]
    brand_voice: Dict[str, Any]
    topic: str
    sections: List[str]
    vector_documents: list[Any]
    blog: Dict[str, Any]
    linkedin: Dict[str, Any]
    images: List[Dict[str, Any]]
    topic_generation_attempted: bool
