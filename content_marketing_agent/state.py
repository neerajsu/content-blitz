"""Session state utilities for navigation."""

from __future__ import annotations

from typing import Any, Literal, Optional

import streamlit as st

from content_marketing_agent.services import project_service

Screen = Literal["home", "project"]
DEFAULT_PROJECT_TITLE = "Untitled"


def init_state() -> None:
    """Initialize shared session state for projects and chats."""
    st.session_state.setdefault("current_screen", "home")
    st.session_state.setdefault("current_project_id", None)
    st.session_state.setdefault("active_chat_id", None)
    st.session_state.setdefault("chat_edit_id", None)


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


def get_current_project() -> Optional[dict[str, Any]]:
    """Return the currently selected project, if any."""
    project_id = st.session_state.get("current_project_id")
    if not project_id:
        return None
    return project_service.get_project(project_id)


def set_active_chat(chat_id: Optional[str]) -> None:
    st.session_state.active_chat_id = chat_id
    st.session_state.chat_edit_id = None
