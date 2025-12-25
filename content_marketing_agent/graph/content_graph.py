"""LangGraph orchestration for the content marketing assistant."""

from __future__ import annotations

from typing import Any, Dict, TypedDict

from typing_extensions import Required, NotRequired

from langgraph.graph import StateGraph, END

from content_marketing_agent.agents.router_agent import classify_intent
from content_marketing_agent.agents.research_agent import run_research
from content_marketing_agent.agents.blog_agent import generate_blog
from content_marketing_agent.agents.linkedin_agent import generate_linkedin
from content_marketing_agent.agents.image_agent import generate_image_assets
from content_marketing_agent.memory.vector_store import VectorStoreManager
from content_marketing_agent.utils.llm_loader import get_chat_model
from content_marketing_agent.utils.embeddings import get_embeddings
from langchain_core.language_models.chat_models import BaseChatModel


class ContentState(TypedDict, total=False):
    """State container for LangGraph."""

    # Required at graph entry
    user_input: Required[str]
    brand: Required[Dict[str, str]]

    # Produced by nodes
    intent: NotRequired[str]
    research: NotRequired[Dict[str, Any]]
    blog: NotRequired[Dict[str, Any]]
    linkedin: NotRequired[Dict[str, Any]]
    image: NotRequired[Dict[str, Any]]
    history: NotRequired[str]
    analysis: NotRequired[Dict[str, Any]]


def build_graph(llm: BaseChatModel | None = None, vector_manager: VectorStoreManager | None = None) -> Any:
    """
    Construct and return the compiled LangGraph graph.

    Args:
        llm: Optional chat model instance to reuse.
        vector_manager: Optional vector store manager instance.

    Returns:
        Compiled LangGraph executor.
    """
    llm = llm or get_chat_model()
    vm = vector_manager or VectorStoreManager(embeddings=get_embeddings())
    graph = StateGraph(ContentState)

    def router_node(state: ContentState) -> ContentState:
        state.setdefault("brand", {"name": "default"})
        intent_data = classify_intent(llm, state["user_input"])
        state["intent"] = intent_data["intent"]
        state.setdefault("analysis", {})["router_reason"] = intent_data.get("reason", "")
        return state

    def research_node(state: ContentState) -> ContentState:
        history = state.get("history", "")
        research_out = run_research(llm, state["user_input"], vm, history=history)
        state["research"] = research_out
        return state

    def blog_node(state: ContentState) -> ContentState:
        summary = state.get("research", {}).get("analysis", {}).get("summary", "")
        history = state.get("history", "")
        blog_out = generate_blog(
            llm,
            topic=state["user_input"],
            research_summary=summary,
            vector_manager=vm,
            brand_name=state["brand"].get("name", "default"),
            history=history,
        )
        state["blog"] = blog_out
        return state

    def linkedin_node(state: ContentState) -> ContentState:
        source = state.get("blog", {}).get("blog_markdown") or state.get("research", {}).get("analysis", {}).get("summary", "")
        history = state.get("history", "")
        linkedin_out = generate_linkedin(
            llm,
            source=source,
            vector_manager=vm,
            topic=state["user_input"],
            history=history,
        )
        state["linkedin"] = linkedin_out
        return state

    def image_node(state: ContentState) -> ContentState:
        image_out = generate_image_assets(
            llm,
            request=state["user_input"],
            vector_manager=vm,
            brand_name=state["brand"].get("name", "default"),
            history=state.get("history", ""),
        )
        state["image"] = image_out
        return state

    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("blog", blog_node)
    graph.add_node("linkedin", linkedin_node)
    graph.add_node("image", image_node)

    def route_edge(state: ContentState) -> str:
        intent = state.get("intent", "mixed")
        if intent == "research":
            return "research"
        if intent == "blog":
            return "blog"
        if intent == "linkedin":
            return "linkedin"
        if intent == "image":
            return "image"
        return "research"  # default path for mixed or unknown

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_edge, {"research": "research", "blog": "blog", "linkedin": "linkedin", "image": "image"})
    graph.add_edge("research", END)
    graph.add_edge("blog", END)
    graph.add_edge("linkedin", END)
    graph.add_edge("image", END)

    return graph.compile()
