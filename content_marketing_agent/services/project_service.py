"""Project service orchestrating repository calls."""

from __future__ import annotations

from typing import Any, Optional

from content_marketing_agent.data_access import chat_repository, project_repository


def create_project(title: str) -> dict[str, Any]:
    """Create a project with the given title."""
    trimmed_title = (title or "").strip()
    title_to_use = trimmed_title or "Untitled"
    return project_repository.create_project(title_to_use)


def list_projects() -> list[dict[str, Any]]:
    """List projects with chat counts for the home view."""
    projects = project_repository.list_projects()
    counts = {proj["id"]: chat_repository.count_chats(proj["id"]) for proj in projects}
    for proj in projects:
        proj["chat_count"] = counts.get(proj["id"], 0)
    return projects


def get_project(project_id: Optional[str]) -> Optional[dict[str, Any]]:
    if not project_id:
        return None
    return project_repository.get_project(project_id)


def update_project_title(project_id: str, title: str) -> None:
    trimmed_title = (title or "").strip() or "Untitled"
    project_repository.update_project_title(project_id, trimmed_title)
