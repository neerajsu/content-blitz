"""Streamlit entry point for the Agentic Content Marketing Assistant."""

from __future__ import annotations

import os
from typing import Any, Dict
from pathlib import Path
import sys

import streamlit as st
from dotenv import load_dotenv

# Ensure package is discoverable when Streamlit changes the working directory
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_marketing_agent.graph.content_graph import build_graph
from content_marketing_agent.memory.conversation_memory import ConversationManager
from content_marketing_agent.memory.vector_store import VectorStoreManager
from content_marketing_agent.utils.embeddings import get_embeddings
from content_marketing_agent.utils.llm_loader import get_chat_model
from content_marketing_agent.home import render_home


load_dotenv()
st.set_page_config(page_title="Agentic Content Marketing Assistant", layout="wide")


def init_state() -> None:
    """Initialize Streamlit session state objects."""
    if "vector_manager" not in st.session_state:
        st.session_state.vector_manager = VectorStoreManager(get_embeddings())
    if "conv_manager" not in st.session_state:
        st.session_state.conv_manager = ConversationManager()
    if "brand" not in st.session_state:
        st.session_state.brand = {"name": "default", "tone": "", "audience": "", "guidelines": ""}
    if "graph" not in st.session_state:
        st.session_state.graph = build_graph(llm=get_chat_model(), vector_manager=st.session_state.vector_manager)
    if "last_outputs" not in st.session_state:
        st.session_state.last_outputs = {"research": {}, "blog": {}, "linkedin": {}, "image": {}, "intent": "", "analysis": {}}
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    if "home_chat_selected" not in st.session_state:
        st.session_state.home_chat_selected = None
    if "home_chat_edit_id" not in st.session_state:
        st.session_state.home_chat_edit_id = None
    if "home_chats" not in st.session_state:
        st.session_state.home_chats = [
            {"id": "c1", "title": "AI trends in 2024", "summary": "Latest AI trends for SaaS companies"},
            {"id": "c2", "title": "Marketing strategies for SaaS", "summary": "Go-to-market and growth ideas"},
            {"id": "c3", "title": "Remote work productivity", "summary": "Tools and rituals for async teams"},
            {"id": "c4", "title": "Blockchain basics", "summary": "Explainer for non-technical leaders"},
            {"id": "c5", "title": "Sustainable business practices", "summary": "Greener ops for startups"},
        ]
    if "home_chat_counter" not in st.session_state:
        st.session_state.home_chat_counter = len(st.session_state.home_chats) + 1


def store_brand_voice(brand: Dict[str, str]) -> None:
    """Persist brand voice guidance into the brand_voice collection."""
    voice_blob = f"Brand: {brand['name']}\nTone: {brand['tone']}\nAudience: {brand['audience']}\nGuidelines: {brand['guidelines']}"
    st.session_state.vector_manager.add_document(
        "brand_voice",
        content=voice_blob,
        metadata={"brand": brand["name"], "tone": brand["tone"], "audience": brand["audience"]},
    )


def run_agents(user_input: str) -> Dict[str, Any]:
    """Execute LangGraph with current state."""
    history_text = "\n".join([f"{role}: {content}" for role, content in st.session_state.conv_manager.as_tuples()])
    state = {
        "user_input": user_input,
        "brand": st.session_state.brand,
        "history": history_text,
    }
    result = st.session_state.graph.invoke(state)
    st.session_state.last_outputs = result

    intent = result.get("intent", "mixed")
    ai_summary = result.get(intent, {}) if isinstance(result.get(intent, {}), dict) else result.get("research", {})
    st.session_state.conv_manager.append(user_input, str(ai_summary)[:5000])
    return result


def render_brand_setup() -> None:
    """Render brand setup section."""
    st.subheader("Brand Setup")
    with st.form("brand_form"):
        name = st.text_input("Brand name", value=st.session_state.brand.get("name", ""))
        tone = st.text_input("Tone", value=st.session_state.brand.get("tone", ""))
        audience = st.text_input("Audience", value=st.session_state.brand.get("audience", ""))
        guidelines = st.text_area("Writing guidelines", value=st.session_state.brand.get("guidelines", ""))
        submitted = st.form_submit_button("Save brand voice")
        if submitted:
            st.session_state.brand = {"name": name or "", "tone": tone or "", "audience": audience or "", "guidelines": guidelines or ""}
            store_brand_voice(st.session_state.brand)
            st.success("Brand voice saved to vector store.")


def render_chat() -> None:
    """Render chat and execution area."""
    st.subheader("Chat Interface")
    user_input = st.text_area("Your request", height=120, placeholder="e.g., Research AI tools for B2B SaaS founders")
    col1, col2 = st.columns([1, 3])
    with col1:
        run_clicked = st.button("Run Agents", type="primary")
    with col2:
        st.markdown("Session brand: **{}** | Tone: **{}** | Audience: **{}**".format(
            st.session_state.brand.get("name", "default"),
            st.session_state.brand.get("tone", "n/a"),
            st.session_state.brand.get("audience", "n/a"),
        ))

    if run_clicked and user_input.strip():
        with st.status("Running agents...", expanded=True) as status:
            result = run_agents(user_input.strip())
            status.update(label=f"Completed: routed to {result.get('intent', 'mixed')}", state="complete")
    elif run_clicked:
        st.warning("Please enter a request.")


def render_outputs() -> None:
    """Render output tabs for research, blog, LinkedIn, and image."""
    st.subheader("Outputs")
    research_tab, blog_tab, linkedin_tab, image_tab = st.tabs(["Research", "Blog", "LinkedIn", "Image"])

    with research_tab:
        research = st.session_state.last_outputs.get("research", {})
        st.write("Query:", research.get("query", ""))
        analysis = research.get("analysis", {}) or {}
        summary = analysis.get("summary", "") or "_No summary available._"
        keywords = analysis.get("keywords", []) or []
        insights = analysis.get("insights", []) or []
        references = analysis.get("references", []) or []

        st.markdown("**Summary**")
        st.markdown(f"> {summary}")

        col_kw, col_insights = st.columns(2)
        with col_kw:
            st.markdown("**Keywords**")
            if keywords:
                st.markdown("\n".join([f"- {kw}" for kw in keywords]))
            else:
                st.caption("No keywords.")
        with col_insights:
            st.markdown("**Insights**")
            if insights:
                st.markdown("\n".join([f"- {ins}" for ins in insights]))
            else:
                st.caption("No insights.")

        st.markdown("**References**")
        if references:
            for idx, ref in enumerate(references, start=1):
                title = ref.get("title") or ref.get("url") or "Reference"
                url = ref.get("url") or ""
                snippet = ref.get("snippet") or ""
                link = f"[{title}]({url})" if url else title
                st.markdown(f"{idx}. {link}\n    - {snippet}")
        else:
            st.caption("No references.")

    with blog_tab:
        blog = st.session_state.last_outputs.get("blog", {})
        if blog:
            st.markdown(f"**Meta Title:** {blog.get('meta_title', '')}")
            st.markdown(f"**Meta Description:** {blog.get('meta_description', '')}")
            st.markdown(blog.get("blog_markdown", ""))
        else:
            st.info("Run a blog intent to see output.")

    with linkedin_tab:
        linkedin = st.session_state.last_outputs.get("linkedin", {})
        st.text_area("Post", value=linkedin.get("post", ""), height=220)
        st.text_area("Carousel", value=linkedin.get("carousel", ""), height=120)

    with image_tab:
        image = st.session_state.last_outputs.get("image", {})
        # Render as read-only so latest agent output is always shown (no sticky session state keys)
        st.text_area("Prompt", value=image.get("prompt", ""), height=100, disabled=True)
        st.text_area("Caption", value=image.get("caption", ""), height=80, disabled=True)
        st.text_area("Alt Text", value=image.get("alt_text", ""), height=80, disabled=True)
        if image.get("image_url"):
            st.write("Image URL:", image["image_url"])
        st.caption("Image generation is stubbed. Integrate your provider in `agents/image_agent.py`.")


def render_history() -> None:
    """Render conversation history."""
    st.subheader("Conversation Memory")
    for role, content in st.session_state.conv_manager.as_tuples():
        st.markdown(f"**{role.title()}:** {content}")


def main() -> None:
    """Main Streamlit entry."""
    init_state()
    st.sidebar.title("Navigation")
    st.session_state.page = st.sidebar.radio("Go to", ["Home", "Agent Work"], index=0 if st.session_state.page == "Home" else 1)

    if st.session_state.page == "Home":
        render_home()
    else:
        st.title("Agentic Content Marketing Assistant")
        st.markdown("Multi-agent system with LangGraph, RAG (brand voice only), and Streamlit UI.")
        render_brand_setup()
        render_chat()
        render_outputs()
        with st.expander("Session Memory"):
            render_history()


if __name__ == "__main__":
    main()
