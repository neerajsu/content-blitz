"""Project detail screen (research, content, and images)."""

from __future__ import annotations

import streamlit as st

from content_marketing_agent.chat import DEFAULT_RESEARCH_MESSAGE, render_chat_detail
from content_marketing_agent.state import (
    DEFAULT_PROJECT_TITLE,
    add_chat_to_project,
    delete_chat,
    get_current_project,
    set_active_chat,
    set_current_project,
    update_chat_title,
    update_project_title,
)


def _render_header(project_id: str, project_title: str) -> None:
    """Render project title and navigation."""
    left, right = st.columns([0.8, 0.2])
    with left:
        new_title = st.text_input(
            "Project title",
            value=project_title or DEFAULT_PROJECT_TITLE,
            key=f"project_title_{project_id}",
        )
        if new_title.strip() and new_title != project_title:
            update_project_title(project_id, new_title)
            st.rerun()
    with right:
        if st.button("Back to Home", key="back_to_home"):
            set_current_project(None)
            st.rerun()

    st.caption("Research, create content, and generate imagery for this project.")


def _render_chat_list(project_id: str, chats: list[dict[str, str]]) -> None:
    left_title_col, left_btn_col = st.columns([4, 1])
    with left_title_col:
        st.subheader("Research")
    with left_btn_col:
        if st.button("New chat", key=f"add_chat_{project_id}", use_container_width=True):
            created = add_chat_to_project(project_id, DEFAULT_RESEARCH_MESSAGE)
            if created:
                st.rerun()

    if not chats:
        st.info("No chats yet. Create a new one to start researching.")
        return

    st.caption("Select a chat to view details.")
    for chat in chats:
        editing = st.session_state.get("chat_edit_id") == chat["id"]
        row_cols = st.columns([0.78, 0.11, 0.11])
        with row_cols[0]:
            summary = chat.get("summary") or "No research yet"
            if editing:
                new_title = st.text_input(
                    "Edit chat title",
                    value=chat.get("title") or "",
                    key=f"edit_title_{chat['id']}",
                    label_visibility="collapsed",
                )
                save = st.button("Save", key=f"save_{chat['id']}")
                if save:
                    title_to_save = new_title or chat.get("title") or "Untitled chat"
                    update_chat_title(project_id, chat["id"], title_to_save, generated=False)
                    st.session_state.chat_edit_id = None
                    st.rerun()
            else:
                display_title = chat.get("title") or "Untitled chat"
                display_summary = summary if summary and summary != "No research yet" else ""
                label = f"{display_title}\n{display_summary}" if display_summary else display_title
                if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                    set_active_chat(chat["id"])
                    st.rerun()
        with row_cols[1]:
            if editing:
                if st.button("✖️", key=f"cancel_{chat['id']}", help="Cancel edit", use_container_width=True):
                    st.session_state.chat_edit_id = None
                    st.rerun()
            else:
                if st.button("✏️", key=f"edit_{chat['id']}", help="Edit chat title", use_container_width=True):
                    st.session_state.chat_edit_id = chat["id"]
                    st.rerun()
        with row_cols[2]:
            if st.button("🗑️", key=f"del_{chat['id']}", help="Delete chat", use_container_width=True):
                delete_chat(project_id, chat["id"])
                st.rerun()


def render_project() -> None:
    """Render the Project screen (previously the Home view)."""
    project = get_current_project()
    if not project:
        st.info("No project selected. Create one from Home to begin.")
        if st.button("Go to Home", key="go_home_from_project"):
            set_current_project(None)
            st.rerun()
        return

    project_id = project["id"]
    _render_header(project_id, project.get("title") or DEFAULT_PROJECT_TITLE)

    selected_chat_id = st.session_state.get("active_chat_id")
    chats = project.get("chats", [])

    if selected_chat_id is None:
        col_left, col_mid, col_right = st.columns([1.1, 1.4, 0.9])

        with col_left:
            _render_chat_list(project_id, chats)

        with col_mid:
            st.subheader("Content Creation")
            st.caption("Content drafting workflows will appear here.")
            st.text_area(
                "Enter your prompt",
                key=f"content_input_{project_id}",
                placeholder="Draft or refine content (coming soon)",
                height=140,
                max_chars=1000,
            )

        with col_right:
            st.subheader("Images")
            st.caption("Image generation workflows will appear here.")
            st.info("No images yet. Generate prompts from your research to see them here.")
    else:
        selected_chat = next((chat for chat in chats if chat.get("id") == selected_chat_id), None)
        if not selected_chat:
            set_active_chat(None)
            st.rerun()
            return
        render_chat_detail(selected_chat, project_id)
