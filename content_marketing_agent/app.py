"""Streamlit entry point for the Agentic Content Marketing Assistant."""

from __future__ import annotations

from pathlib import Path
import sys
import logging

import streamlit as st
from dotenv import load_dotenv

# Ensure package is discoverable when Streamlit changes the working directory
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_marketing_agent.home import render_home
from content_marketing_agent.project import render_project
from content_marketing_agent.services.bootstrap import bootstrap_storage
from content_marketing_agent.state import init_state


load_dotenv()
st.set_page_config(page_title="Agentic Content Marketing Assistant", layout="wide")
# Simple logging to surface agent decisions in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


def main() -> None:
    """Main Streamlit entry."""
    bootstrap_storage()
    init_state()
    if st.session_state.current_screen == "project":
        render_project()
    else:
        render_home()


if __name__ == "__main__":
    main()
