"""Home screen that lists available projects."""

from __future__ import annotations

import streamlit as st

from content_marketing_agent.services import brand_voice_service, project_service
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

    brand_voice = st.session_state.get("brand_voice") or brand_voice_service.get_brand_voice()
    with st.container(border=True):
        st.subheader("Brand Voice")
        with st.form("brand_voice_form", clear_on_submit=False):
            brand = st.text_input("Brand", value=brand_voice.get("brand", ""), max_chars=120)
            tone = st.text_input("Tone", value=brand_voice.get("tone", ""), max_chars=200)
            audience = st.text_input("Audience", value=brand_voice.get("audience", ""), max_chars=200)
            guidelines = st.text_area(
                "Writing Guidelines", value=brand_voice.get("guidelines", ""), height=100, max_chars=800
            )
            saved = st.form_submit_button("Save brand voice", use_container_width=True)

        if saved:
            saved_profile = brand_voice_service.save_brand_voice(brand, tone, audience, guidelines)
            st.session_state["brand_voice"] = saved_profile
            st.success("Brand voice saved.")

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
