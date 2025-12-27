"""Home screen that lists available projects."""

from __future__ import annotations

import streamlit as st

from content_marketing_agent.services import project_service
from content_marketing_agent.state import DEFAULT_PROJECT_TITLE, set_current_project


def _render_create_tile() -> None:
    card = st.container(height=170, border=True)
    with card:
        st.markdown("#### Create New Project")
        st.caption("Start a blank project workspace.")
        if st.button("Create Project", key="create_project", use_container_width=True):
            project = project_service.create_project(DEFAULT_PROJECT_TITLE)
            set_current_project(project["id"])
            st.rerun()


def _render_project_tile(project: dict[str, str]) -> None:
    card = st.container(height=170, border=True)
    with card:
        st.markdown(f"#### {project.get('title') or DEFAULT_PROJECT_TITLE}")
        chat_count = project.get("chat_count", 0)
        st.caption(f"{chat_count} chat{'s' if chat_count != 1 else ''}")
        if st.button("Open Project", key=f"open_{project['id']}", use_container_width=True):
            set_current_project(project["id"])
            st.rerun()


def render_home() -> None:
    """Render the Home screen with a grid of projects."""
    st.title("Home")
    st.caption("Jump into an existing project or start a new one.")

    projects = project_service.list_projects()
    tiles: list[dict] = [{"type": "create"}] + [{"type": "project", "data": proj} for proj in projects]

    if not projects:
        st.write("You don't have any projects yet. Create one to begin.")

    for row_start in range(0, len(tiles), 4):
        cols = st.columns(4)
        for offset in range(4):
            tile_index = row_start + offset
            if tile_index >= len(tiles):
                continue
            tile = tiles[tile_index]
            with cols[offset]:
                if tile["type"] == "create":
                    _render_create_tile()
                else:
                    _render_project_tile(tile["data"])
