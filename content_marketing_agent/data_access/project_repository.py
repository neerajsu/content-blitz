"""Project persistence helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from content_marketing_agent.data_access.database import get_collection


def _projects():
    return get_collection("projects")


def create_project(title: str) -> dict[str, Any]:
    """Insert a new project."""
    project_id = uuid4().hex
    now = datetime.utcnow()
    doc = {
        "_id": project_id,
        "id": project_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
    }
    _projects().insert_one(doc)
    return doc


def list_projects() -> list[dict[str, Any]]:
    """Return all projects sorted by creation time."""
    cursor = _projects().find().sort("created_at", -1)
    return [dict(doc) for doc in cursor]


def get_project(project_id: str) -> Optional[dict[str, Any]]:
    """Fetch a project by id."""
    doc = _projects().find_one({"_id": project_id})
    return dict(doc) if doc else None


def update_project_title(project_id: str, title: str) -> None:
    """Update a project's title."""
    now = datetime.utcnow()
    _projects().update_one({"_id": project_id}, {"$set": {"title": title, "updated_at": now}})
