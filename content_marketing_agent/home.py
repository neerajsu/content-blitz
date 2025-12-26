"""Home page layout for the Content Marketing Assistant UI."""

from __future__ import annotations

import streamlit as st

from content_marketing_agent.chat import render_chat_detail


def render_home() -> None:
    """Render the Home page with Research, Content Creation, and Images columns."""
    st.title("Home")
    st.caption("Create research chats and iterate on outputs with the chatbot.")

    chats = st.session_state.get("home_chats", [])

    if st.session_state.home_chat_selected is None:
        col_left, col_mid, col_right = st.columns([1.1, 1.4, 0.9])
        # Left: Research chats list
        with col_left:
            left_title_col, left_btn_col = st.columns([4, 1])
            with left_title_col:
                st.subheader("Research")
            with left_btn_col:
                if st.button("New chat", key="add_chat", use_container_width=True):
                    next_id = f"c{st.session_state.home_chat_counter}"
                    st.session_state.home_chat_counter += 1
                    new_chat = {"id": next_id, "title": "", "summary": "No research yet", "title_generated": False}
                    st.session_state.home_chats.append(new_chat)
                    st.session_state.home_chat_selected = new_chat
                    st.session_state.chat_histories.setdefault(next_id, [])
                    st.session_state.research_outputs.setdefault(
                        next_id, "Research something with the chatbot to populate this section."
                    )
                    st.rerun()

            if not chats:
                st.info("No chats yet. Create a new one to start researching.")
            else:
                st.caption("Select a chat to view details.")
                for chat in chats:
                    editing = st.session_state.get("home_chat_edit_id") == chat["id"]
                    row_cols = st.columns([0.82, 0.09, 0.09])
                    with row_cols[0]:
                        summary = chat.get("summary") or "No research yet"
                        if editing:
                            new_title = st.text_input(
                                "Edit chat title",
                                value=chat["title"],
                                key=f"edit_title_{chat['id']}",
                                label_visibility="collapsed",
                            )
                            save = st.button("Save", key=f"save_{chat['id']}")
                            if save:
                                chat["title"] = new_title or chat["title"]
                                chat["title_generated"] = True
                                st.session_state.home_chat_edit_id = None
                                st.rerun()
                        else:
                            display_summary = summary if summary and summary != "No research yet" else ""
                            display_title = chat.get("title") or "Untitled chat"
                            label = f"{display_title}\n{display_summary}" if display_summary else display_title
                            if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                                st.session_state.home_chat_selected = chat
                                st.rerun()
                    with row_cols[1]:
                        if editing:
                            if st.button("✖️", key=f"cancel_{chat['id']}", use_container_width=True):
                                st.session_state.home_chat_edit_id = None
                                st.rerun()
                        else:
                            if st.button("✏️", key=f"edit_{chat['id']}", use_container_width=True):
                                st.session_state.home_chat_edit_id = chat["id"]
                                st.rerun()
                    with row_cols[2]:
                        if st.button("🗑️", key=f"del_{chat['id']}", use_container_width=True):
                            st.session_state.home_chats = [c for c in st.session_state.home_chats if c["id"] != chat["id"]]
                            st.session_state.chat_histories.pop(chat["id"], None)
                            st.session_state.research_outputs.pop(chat["id"], None)
                            st.session_state.research_structured.pop(chat["id"], None)
                            st.rerun()

        # Middle: Content creation
        with col_mid:
            st.subheader("Content Creation")
            st.caption("Content drafting workflows will appear here.")
            st.text_area(
                "Enter your prompt",
                key="home_content_input",
                placeholder="Draft or refine content (coming soon)",
                height=140,
                max_chars=1000,
            )

        # Right: Images
        with col_right:
            st.subheader("Images")
            st.caption("Image generation workflows will appear here.")
            st.info("No images yet. Generate prompts from your research to see them here.")
    else:
        selected = st.session_state.home_chat_selected
        render_chat_detail(selected)
