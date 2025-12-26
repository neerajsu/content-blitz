"""Chat detail view for Home page."""

from __future__ import annotations

import streamlit as st


def render_chat_detail(selected_chat: dict, chat_history: list[tuple[str, str]], research_markdown: str) -> None:
    """Render the two-column chat + research output view for a selected chat."""
    back_col, _ = st.columns([0.2, 0.8])
    with back_col:
        if st.button("← Back to chats", key="back_to_chats"):
            st.session_state.home_chat_selected = None
            st.rerun()

    st.markdown(f"**{selected_chat.get('title', 'Chat')}**")

    chat_col, research_col = st.columns([1.1, 1.3])
    with chat_col:
        st.subheader("Chat")
        chat_container = st.container(height=400, border=True)
        with chat_container:
            for role, msg in chat_history:
                if role.lower() == "you":
                    chat_container.chat_message("user").write(msg)
                else:
                    chat_container.chat_message("assistant").write(msg)
        st.text_area(
            "Enter your prompt…",
            key="home_chat_input",
            placeholder="Type to continue the chat",
            height=140,
            max_chars=None,
        )
        if st.button("Submit", key="home_chat_submit"):
            st.caption("Message submitted (stubbed). Integrate chat handling to append responses.")

    with research_col:
        st.subheader("Research Output")
        output_box = st.container(height=480, border=True)
        with output_box:
            st.markdown(research_markdown)
