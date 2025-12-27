"""Chat persistence helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from content_marketing_agent.data_access.database import get_collection


def _chats():
    return get_collection("chats")


def create_chat(project_id: str) -> dict[str, Any]:
    """Insert a chat belonging to a project."""
    chat_id = uuid4().hex
    now = datetime.utcnow()
    doc = {
        "_id": chat_id,
        "id": chat_id,
        "project_id": project_id,
        "title": "",
        "summary": "No research yet",
        "title_generated": False,
        "created_at": now,
        "updated_at": now,
    }
    _chats().insert_one(doc)
    return doc


def get_chat(chat_id: str) -> Optional[dict[str, Any]]:
    doc = _chats().find_one({"_id": chat_id})
    return dict(doc) if doc else None


def list_chats(project_id: str) -> list[dict[str, Any]]:
    """List chats for a project."""
    cursor = _chats().find({"project_id": project_id}).sort("created_at", -1)
    return [dict(doc) for doc in cursor]


def delete_chat(chat_id: str) -> None:
    _chats().delete_one({"_id": chat_id})


def update_chat_title(chat_id: str, title: str, generated: bool = False) -> None:
    now = datetime.utcnow()
    _chats().update_one({"_id": chat_id}, {"$set": {"title": title, "title_generated": generated, "updated_at": now}})


def update_chat_summary(chat_id: str, summary: str) -> None:
    now = datetime.utcnow()
    _chats().update_one({"_id": chat_id}, {"$set": {"summary": summary, "updated_at": now}})


def count_chats(project_id: str) -> int:
    return _chats().count_documents({"project_id": project_id})
