"""Streamlit entry point for the Agentic Content Marketing Assistant."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st
from dotenv import load_dotenv

# Ensure package is discoverable when Streamlit changes the working directory
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_marketing_agent.home import render_home


load_dotenv()
st.set_page_config(page_title="Agentic Content Marketing Assistant", layout="wide")


def init_state() -> None:
    """Initialize Streamlit session state for the Home page."""
    if "home_chat_selected" not in st.session_state:
        st.session_state.home_chat_selected = None
    if "home_chat_edit_id" not in st.session_state:
        st.session_state.home_chat_edit_id = None
    if "home_chats" not in st.session_state:
        st.session_state.home_chats = []
    if "home_chat_counter" not in st.session_state:
        st.session_state.home_chat_counter = len(st.session_state.home_chats) + 1
    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories: dict[str, list[tuple[str, str]]] = {}
    if "research_outputs" not in st.session_state:
        st.session_state.research_outputs: dict[str, str] = {}
    if "research_structured" not in st.session_state:
        st.session_state.research_structured: dict[str, dict] = {}


def main() -> None:
    """Main Streamlit entry."""
    init_state()
    render_home()


if __name__ == "__main__":
    main()
