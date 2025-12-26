"""Home page layout for the Content Marketing Assistant UI."""

from __future__ import annotations

import streamlit as st

from content_marketing_agent.chat import render_chat_detail


def render_home() -> None:
    """Render the Home page with Research, Content Creation, and Images columns (dummy data)."""
    st.title("Home")
    st.caption("Snapshots for research, content creation, and images. Data below is dummy placeholder content.")

    chats = st.session_state.get("home_chats", [])
    dummy_chat_history = [
        ("You", "Best marketing strategies for SaaS?"),
        ("Assistant", "Content marketing, SEO, product-led growth, and community building are essential."),
    ]
    dummy_research_md = """## Research Output

### Research Summary
This is the research output for the selected chat. The content here is formatted using **Markdown** and is fully scrollable.

### Key Findings
1. **Point One**: This is an important finding from the research
2. **Point Two**: Another crucial insight discovered
3. **Point Three**: Additional valuable information

### Detailed Analysis
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
"""
    dummy_content_md = """# Sample Content

This is a **markdown editor** where you can create content for LinkedIn or Blog posts.

## Features
- Write in markdown
- Preview your content
- Easy formatting

### Example List
1. First item
2. Second item
3. Third item

*Start editing to create your content!*"""
    dummy_images = [
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85",
        "https://images.unsplash.com/photo-1501004318641-b39e6451bec6",
        "https://images.unsplash.com/photo-1501785888041-af3ef285b470",
        "https://images.unsplash.com/photo-1462331940025-496dfbfc7564",
        "https://images.unsplash.com/photo-1448932223592-d1fc686e76ea",
        "https://images.unsplash.com/photo-1433838552652-f9a46b332c40",
    ]

    if st.session_state.home_chat_selected is None:
        col_left, col_mid, col_right = st.columns([1.1, 1.4, 0.9])
        # Left: Research chats list
        with col_left:
            left_title_col, left_btn_col = st.columns([4, 1])
            with left_title_col:
                st.subheader("Research")
            with left_btn_col:
                if st.button("➕", key="add_chat_placeholder"):
                    next_id = f"c{st.session_state.home_chat_counter}"
                    st.session_state.home_chat_counter += 1
                    st.session_state.home_chats.append(
                        {"id": next_id, "title": f"New chat {next_id}", "summary": "Edit this summary"}
                    )

            st.caption("Select a chat to view details.")
            for chat in chats:
                row_cols = st.columns([0.75, 0.1, 0.1])
                editing = st.session_state.get("home_chat_edit_id") == chat["id"]
                with row_cols[0]:
                    if editing:
                        new_title = st.text_input(
                            "Title",
                            value=chat["title"],
                            key=f"edit_title_{chat['id']}",
                            label_visibility="collapsed",
                        )
                        save = st.button("Save", key=f"save_{chat['id']}")
                        if save:
                            chat["title"] = new_title or chat["title"]
                            st.session_state.home_chat_edit_id = None
                            st.rerun()
                    else:
                        if st.button(f"{chat['title']}\n{chat['summary']}", key=f"chat_{chat['id']}"):
                            st.session_state.home_chat_selected = chat
                            st.rerun()
                with row_cols[1]:
                    if not editing and st.button("✏️", key=f"edit_{chat['id']}"):
                        st.session_state.home_chat_edit_id = chat["id"]
                        st.rerun()
                with row_cols[2]:
                    if st.button("🗑️", key=f"del_{chat['id']}"):
                        st.session_state.home_chats = [c for c in st.session_state.home_chats if c["id"] != chat["id"]]
                        if st.session_state.get("home_chat_edit_id") == chat["id"]:
                            st.session_state.home_chat_edit_id = None

        # Middle: Content creation
        with col_mid:
            st.subheader("Content Creation")
            content_tab = st.segmented_control("Mode", options=["LinkedIn", "Blog"], key="home_content_mode")
            st.markdown(dummy_content_md, help=f"Current mode: {content_tab}")
            st.text_area(
                "Enter your prompt…",
                key="home_content_input",
                placeholder="Draft or refine content (mock)",
                height=140,
                max_chars=1000,
            )

        # Right: Images
        with col_right:
            st.subheader("Images")
            st.caption("Dummy gallery")
            rows = [dummy_images[i : i + 2] for i in range(0, len(dummy_images), 2)]
            for row in rows:
                c1, c2 = st.columns(2)
                if len(row) > 0:
                    c1.image(row[0])
                if len(row) > 1:
                    c2.image(row[1])
    else:
        selected = st.session_state.home_chat_selected
        render_chat_detail(selected, dummy_chat_history, dummy_research_md)
