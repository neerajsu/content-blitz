"""Research output persistence helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from content_marketing_agent.data_access.database import get_collection


def _research_outputs():
    return get_collection("research_outputs")


def upsert_research_output(
    project_id: str, chat_id: str, markdown: str, structured: dict[str, Any], summary: str
) -> dict[str, Any]:
    """Create or replace a research output for a chat."""
    now = datetime.utcnow()
    doc = {
        "project_id": project_id,
        "chat_id": chat_id,
        "markdown": markdown,
        "structured": structured,
        "summary": summary,
        "updated_at": now,
    }
    _research_outputs().update_one({"chat_id": chat_id}, {"$set": doc}, upsert=True)
    return doc


def get_research_output(chat_id: str) -> Optional[dict[str, Any]]:
    doc = _research_outputs().find_one({"chat_id": chat_id})
    return dict(doc) if doc else None


def delete_research_output(chat_id: str) -> None:
    _research_outputs().delete_one({"chat_id": chat_id})


def list_research_outputs(project_id: str) -> list[dict[str, Any]]:
    """
    Return all research outputs for a project.

    Only pulls the fields needed for downstream content generation.
    """
    cursor = _research_outputs().find(
        {"project_id": project_id},
        {"chat_id": 1, "project_id": 1, "summary": 1, "structured": 1},
    )
    return [dict(doc) for doc in cursor]
