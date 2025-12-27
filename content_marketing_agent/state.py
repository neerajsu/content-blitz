"""Session state utilities for projects and chats."""

from __future__ import annotations

from typing import Any, Literal, Optional

import streamlit as st

Screen = Literal["home", "project"]
DEFAULT_PROJECT_TITLE = "Untitled"


def init_state() -> None:
    """Initialize shared session state for projects and chats."""
    st.session_state.setdefault("projects", [])
    st.session_state.setdefault("project_counter", len(st.session_state["projects"]) + 1)
    st.session_state.setdefault("current_screen", "home")
    st.session_state.setdefault("current_project_id", None)
    st.session_state.setdefault("active_chat_id", None)
    st.session_state.setdefault("chat_edit_id", None)
    st.session_state.setdefault("chat_histories", {})
    st.session_state.setdefault("research_outputs", {})
    st.session_state.setdefault("research_structured", {})


def _ensure_project_defaults(project: dict[str, Any]) -> dict[str, Any]:
    project.setdefault("title", DEFAULT_PROJECT_TITLE)
    project.setdefault("chats", [])
    project.setdefault("chat_counter", len(project["chats"]) + 1)
    return project


def list_projects() -> list[dict[str, Any]]:
    """Return the projects list with defaults applied."""
    projects = st.session_state.get("projects", [])
    return [_ensure_project_defaults(proj) for proj in projects]


def set_screen(screen: Screen) -> None:
    st.session_state.current_screen = screen


def set_current_project(project_id: Optional[str]) -> None:
    st.session_state.current_project_id = project_id
    st.session_state.active_chat_id = None
    st.session_state.chat_edit_id = None
    if project_id:
        set_screen("project")
    else:
        set_screen("home")


def create_project(title: str = DEFAULT_PROJECT_TITLE) -> dict[str, Any]:
    """Create a new project and switch to it."""
    project_id = f"p{st.session_state.project_counter}"
    st.session_state.project_counter += 1
    project = _ensure_project_defaults({"id": project_id, "title": title or DEFAULT_PROJECT_TITLE, "chats": []})
    st.session_state.projects.append(project)
    set_current_project(project_id)
    return project


def get_current_project() -> Optional[dict[str, Any]]:
    """Return the currently selected project, if any."""
    project_id = st.session_state.get("current_project_id")
    if not project_id:
        return None
    return get_project(project_id)


def get_project(project_id: str) -> Optional[dict[str, Any]]:
    for project in list_projects():
        if project.get("id") == project_id:
            return project
    return None


def update_project_title(project_id: str, title: str) -> None:
    new_title = (title or "").strip() or DEFAULT_PROJECT_TITLE
    updated_projects: list[dict[str, Any]] = []
    for project in list_projects():
        if project.get("id") == project_id:
            project["title"] = new_title
        updated_projects.append(project)
    st.session_state.projects = updated_projects


def get_chat(project_id: str, chat_id: str) -> Optional[dict[str, Any]]:
    project = get_project(project_id)
    if not project:
        return None
    return next((chat for chat in project["chats"] if chat.get("id") == chat_id), None)


def add_chat_to_project(project_id: str, default_research_message: str) -> Optional[dict[str, Any]]:
    project = get_project(project_id)
    if not project:
        return None
    next_id = f"{project_id}_c{project['chat_counter']}"
    project["chat_counter"] += 1
    new_chat = {"id": next_id, "title": "", "summary": "No research yet", "title_generated": False}
    project["chats"].append(new_chat)
    st.session_state.chat_histories.setdefault(next_id, [])
    st.session_state.research_outputs.setdefault(next_id, default_research_message)
    st.session_state.research_structured.setdefault(next_id, {})
    st.session_state.active_chat_id = new_chat["id"]
    return new_chat


def set_active_chat(chat_id: Optional[str]) -> None:
    st.session_state.active_chat_id = chat_id
    st.session_state.chat_edit_id = None


def delete_chat(project_id: str, chat_id: str) -> None:
    project = get_project(project_id)
    if not project:
        return
    project["chats"] = [chat for chat in project["chats"] if chat.get("id") != chat_id]
    st.session_state.chat_histories.pop(chat_id, None)
    st.session_state.research_outputs.pop(chat_id, None)
    st.session_state.research_structured.pop(chat_id, None)
    if st.session_state.active_chat_id == chat_id:
        st.session_state.active_chat_id = None
    if st.session_state.chat_edit_id == chat_id:
        st.session_state.chat_edit_id = None


def update_chat_title(project_id: str, chat_id: str, title: str, generated: bool = False) -> None:
    project = get_project(project_id)
    if not project:
        return
    updated_chats: list[dict[str, Any]] = []
    for chat in project["chats"]:
        if chat.get("id") == chat_id:
            chat["title"] = title
            if generated:
                chat["title_generated"] = True
        updated_chats.append(chat)
    project["chats"] = updated_chats


def update_chat_summary(project_id: str, chat_id: str, summary: str) -> None:
    trimmed = (summary or "").strip()
    if not trimmed:
        return
    snippet = trimmed.splitlines()[0][:120]
    project = get_project(project_id)
    if not project:
        return
    updated: list[dict[str, Any]] = []
    for chat in project["chats"]:
        if chat.get("id") == chat_id:
            chat["summary"] = snippet
        updated.append(chat)
    project["chats"] = updated
