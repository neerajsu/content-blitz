"""LangGraph orchestration for research flows."""

from __future__ import annotations

from typing import Any, Dict, TypedDict

from langgraph.graph import StateGraph, END

from content_marketing_agent.agents.research_agent import ResearchState, research_step
from content_marketing_agent.agents.title_agent import TitleState, generate_title


def build_research_graph():
    """Compile and return a runnable research graph."""
    graph = StateGraph(ResearchState)
    graph.add_node("research", research_step)
    graph.set_entry_point("research")
    graph.add_edge("research", END)
    return graph.compile()


def build_title_graph():
    """Compile and return a runnable title-generation graph."""
    graph = StateGraph(TitleState)
    graph.add_node("title", generate_title)
    graph.set_entry_point("title")
    graph.add_edge("title", END)
    return graph.compile()
