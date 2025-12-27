"""Message persistence helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from content_marketing_agent.data_access.database import get_collection


def _messages():
    return get_collection("messages")


def add_message(project_id: str, chat_id: str, role: str, content: str) -> dict[str, Any]:
    """Insert a message for a chat."""
    message_id = uuid4().hex
    now = datetime.utcnow()
    doc = {
        "_id": message_id,
        "id": message_id,
        "project_id": project_id,
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "created_at": now,
    }
    _messages().insert_one(doc)
    return doc


def list_messages(chat_id: str, limit: Optional[int] = None) -> list[dict[str, Any]]:
    """List messages for a chat ordered by time."""
    cursor = _messages().find({"chat_id": chat_id}).sort("created_at", 1)
    if limit:
        cursor = cursor.limit(limit)
    return [dict(doc) for doc in cursor]


def delete_messages_for_chat(chat_id: str) -> None:
    """Remove all messages belonging to a chat."""
    _messages().delete_many({"chat_id": chat_id})
