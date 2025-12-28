"""Project detail screen (research, content, and images)."""

from __future__ import annotations

import json
import logging

import streamlit as st

from content_marketing_agent.chat import DEFAULT_RESEARCH_MESSAGE, render_chat_detail
from content_marketing_agent.graph.content_graph import build_content_graph
from content_marketing_agent.services import chat_service, project_service
from content_marketing_agent.state import DEFAULT_PROJECT_TITLE, get_current_project, set_active_chat, set_current_project

logger = logging.getLogger(__name__)


@st.cache_resource
def _get_content_graph():
    """Cache the compiled content graph."""
    return build_content_graph()


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
            project_service.update_project_title(project_id, new_title)
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
            created = chat_service.add_new_chat(project_id, DEFAULT_RESEARCH_MESSAGE)
            if created:
                set_active_chat(created["id"])
                st.rerun()

    if not chats:
        st.info("No chats yet. Create a new one to start researching.")
        return

    st.caption("Select a chat to view details.")
    for chat in chats:
        editing = st.session_state.get("chat_edit_id") == chat["id"]
        edit_key = f"edit_title_{chat['id']}"
        row_cols = st.columns([0.78, 0.11, 0.11])
        with row_cols[0]:
            summary = chat.get("summary") or "No research yet"
            if editing:
                current_title = chat.get("title") or "Untitled chat"
                new_title = st.text_input(
                    "Edit chat title",
                    value=st.session_state.get(edit_key, current_title),
                    key=edit_key,
                    label_visibility="collapsed",
                )
                save = st.button("Save", key=f"save_{chat['id']}")
                if save:
                    title_to_save = (new_title or "").strip() or "Untitled chat"
                    chat_service.update_chat_title(chat["id"], title_to_save, generated=False)
                    st.session_state.chat_edit_id = None
                    st.session_state.pop(edit_key, None)
                    st.rerun()
            else:
                display_title = chat.get("title") or "Untitled chat"
                if st.button(display_title, key=f"chat_{chat['id']}", use_container_width=True):
                    set_active_chat(chat["id"])
                    st.rerun()
        with row_cols[1]:
            if editing:
                if st.button("Cancel", key=f"cancel_{chat['id']}", help="Cancel edit", use_container_width=True):
                    st.session_state.chat_edit_id = None
                    st.session_state.pop(edit_key, None)
                    st.rerun()
            else:
                if st.button("Edit", key=f"edit_{chat['id']}", help="Edit chat title", use_container_width=True):
                    st.session_state.chat_edit_id = chat["id"]
                    st.session_state[edit_key] = chat.get("title") or "Untitled chat"
                    st.rerun()
        with row_cols[2]:
            if st.button("Delete", key=f"del_{chat['id']}", help="Delete chat", use_container_width=True):
                chat_service.delete_chat(project_id, chat["id"])
                if st.session_state.active_chat_id == chat["id"]:
                    set_active_chat(None)
                if st.session_state.chat_edit_id == chat["id"]:
                    st.session_state.chat_edit_id = None
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
    chats = chat_service.list_chats(project_id)

    if selected_chat_id is None:
        col_left, col_mid, col_right = st.columns([1.1, 1.4, 0.9])

        with col_left:
            _render_chat_list(project_id, chats)

        with col_mid:
            st.subheader("Content Creation")
            st.caption("Draft LinkedIn posts/carousels or blog content.")

            linkedin_post_key = f"linkedin_post_{project_id}"
            linkedin_carousel_key = f"linkedin_carousel_{project_id}"
            blog_content_key = f"blog_markdown_{project_id}"
            meta_title_key = f"blog_meta_title_{project_id}"
            meta_description_key = f"blog_meta_description_{project_id}"

            for key in [linkedin_post_key, linkedin_carousel_key, blog_content_key, meta_title_key, meta_description_key]:
                st.session_state.setdefault(key, "")

            with st.form(key=f"content_form_{project_id}", clear_on_submit=False):
                user_prompt = st.text_area(
                    "Enter your prompt",
                    key=f"content_prompt_{project_id}",
                    placeholder="Enter your prompt...",
                    height=80,
                    max_chars=1000,
                )
                submitted = st.form_submit_button("Generate content")
                if submitted:
                    trimmed = (user_prompt or "").strip()
                    if not trimmed:
                        st.warning("Please enter a prompt before generating content.")
                    else:
                        with st.spinner("Generating content from research outputs..."):
                            graph = _get_content_graph()
                            try:
                                state = graph.invoke(
                                    {
                                        "project_id": project_id,
                                        "project_title": project.get("title") or DEFAULT_PROJECT_TITLE,
                                        "prompt": trimmed,
                                    }
                                )
                            except Exception as exc:
                                st.error(f"Content generation failed: {exc}")
                                state = {}

                        if isinstance(state, dict):
                            linkedin_result = state.get("linkedin") or {}
                            blog_result = state.get("blog") or {}

                            logger.info(
                                "Content graph completed. Has blog: %s, has linkedin: %s",
                                bool(blog_result),
                                bool(linkedin_result),
                            )

                            st.session_state[linkedin_post_key] = linkedin_result.get("post", "")
                            carousel_val = linkedin_result.get("carousel", "")
                            if isinstance(carousel_val, (dict, list)):
                                carousel_val = json.dumps(carousel_val, indent=2)
                            st.session_state[linkedin_carousel_key] = carousel_val or ""

                            st.session_state[blog_content_key] = blog_result.get("blog_markdown", "")
                            st.session_state[meta_title_key] = blog_result.get("meta_title", "")
                            st.session_state[meta_description_key] = blog_result.get("meta_description", "")

                            if not (st.session_state[linkedin_post_key] or st.session_state[blog_content_key]):
                                st.warning("Content graph ran but returned empty results. Check logs for details.")
                            else:
                                st.success("Content generated. Tabs updated with latest outputs.")
                            st.rerun()
                        else:
                            st.error("Content generation did not return any state. Check logs for details.")

            tab_linkedin, tab_blog = st.tabs(["LinkedIn", "Blog"])

            with tab_linkedin:
                st.text_area(
                    "Post (Markdown)",
                    key=linkedin_post_key,
                    height=220,
                    placeholder="No content yet.",
                )
                st.text_area(
                    "Carousel (JSON)",
                    key=linkedin_carousel_key,
                    height=200,
                    placeholder='No content yet.',
                )

            with tab_blog:
                blog_content = st.session_state.get(blog_content_key, "")
                st.text_input("Meta title", key=meta_title_key, disabled=True)
                st.text_area(
                    "Meta description",
                    key=meta_description_key,
                    height=80,
                    disabled=True,
                )
                st.markdown("**Blog Content (Markdown)**")
                st.markdown(blog_content or "_No blog content yet._")

        with col_right:
            st.subheader("Images")
            st.caption("Image generation workflows will appear here.")
            st.info("No images yet. Generate prompts from your research to see them here.")
    else:
        selected_chat = chat_service.get_chat(selected_chat_id)
        if not selected_chat or selected_chat.get("project_id") != project_id:
            set_active_chat(None)
            st.rerun()
            return
        render_chat_detail(selected_chat, project_id)
