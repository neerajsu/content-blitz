"""LangGraph orchestration for research and content flows."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from content_marketing_agent.agents.content_agents import (
    blog_agent_node,
    content_orchestrator_agent,
    intent_agent,
    linkedin_agent_node,
    topic_and_section_generator_agent,
    topic_and_sections_agent,
)
from content_marketing_agent.agents.guard_agent import guard_relevance
from content_marketing_agent.agents.research_agent import ResearchState, research_step
from content_marketing_agent.agents.title_agent import TitleState, generate_title
from content_marketing_agent.graph.content_state import ContentState

logger = logging.getLogger(__name__)


def _content_router(state: ContentState):
    """Route content graph edges based on collected state."""
    if not state.get("intent"):
        logger.info("Routing: no intent detected yet -> intent_agent")
        return "intent_agent"

    topic = (state.get("topic") or "").strip()
    sections = state.get("sections") or []
    attempted = state.get("topic_generation_attempted", False)
    if (not topic or not sections) and not attempted:
        logger.info("Routing: missing topic/sections -> topic_and_section_generator_agent")
        return "topic_and_section_generator_agent"

    intents = [intent.lower() for intent in state.get("intent", [])]
    if "blog" in intents and not state.get("blog"):
        logger.info("Routing: blog intent detected -> blog_agent")
        return "blog_agent"
    if "linkedin" in intents and not state.get("linkedin"):
        logger.info("Routing: LinkedIn intent detected -> linkedin_agent")
        return "linkedin_agent"

    logger.info("Routing: all requested content generated -> END")
    return END


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


def build_content_graph():
    """Compile the content generation graph with orchestrated agents."""
    graph = StateGraph(ContentState)
    graph.add_node("content_orchestrator_agent", content_orchestrator_agent)
    graph.add_node("intent_agent", intent_agent)
    graph.add_node("topic_and_sections_agent", topic_and_sections_agent)
    graph.add_node("topic_and_section_generator_agent", topic_and_section_generator_agent)
    graph.add_node("blog_agent", blog_agent_node)
    graph.add_node("linkedin_agent", linkedin_agent_node)

    graph.set_entry_point("content_orchestrator_agent")
    graph.add_edge("intent_agent", "topic_and_sections_agent")
    graph.add_edge("topic_and_sections_agent", "content_orchestrator_agent")
    graph.add_edge("topic_and_section_generator_agent", "content_orchestrator_agent")
    graph.add_edge("blog_agent", "content_orchestrator_agent")
    graph.add_edge("linkedin_agent", "content_orchestrator_agent")

    graph.add_conditional_edges(
        "content_orchestrator_agent",
        _content_router,
        {
            "intent_agent": "intent_agent",
            "topic_and_section_generator_agent": "topic_and_section_generator_agent",
            "blog_agent": "blog_agent",
            "linkedin_agent": "linkedin_agent",
            END: END,
        },
    )

    return graph.compile()
