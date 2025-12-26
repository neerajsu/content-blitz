"""LangGraph orchestration for research flows."""

from __future__ import annotations

from typing import Any, Dict, TypedDict

from langgraph.graph import StateGraph, END

from content_marketing_agent.agents.research_agent import ResearchState, research_step
from content_marketing_agent.agents.title_agent import TitleState, generate_title
from content_marketing_agent.agents.guard_agent import guard_relevance


def build_research_graph():
    """Compile and return a runnable research graph with guard."""
    graph = StateGraph(ResearchState)
    graph.add_node("guard", guard_relevance)
    graph.add_node("research", research_step)
    graph.set_entry_point("guard")
    graph.add_conditional_edges(
        "guard",
        lambda state: "research" if state.get("allowed", True) else END,
        {"research": "research", END: END},
    )
    graph.add_edge("research", END)
    return graph.compile()


def build_title_graph():
    """Compile and return a runnable title-generation graph."""
    graph = StateGraph(TitleState)
    graph.add_node("title", generate_title)
    graph.set_entry_point("title")
    graph.add_edge("title", END)
    return graph.compile()
