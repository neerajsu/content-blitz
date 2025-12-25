"""Blog writing agent that applies brand voice via RAG."""

from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.blog_prompt import BLOG_PROMPT
from content_marketing_agent.memory.vector_store import VectorStoreManager


def fetch_brand_voice(vector_manager: VectorStoreManager, brand_name: str) -> str:
    """Retrieve brand voice guidance from FAISS; returns concatenated snippets."""
    docs = vector_manager.search("brand_voice", brand_name, k=3)
    if not docs:
        return "Maintain a consistent professional yet friendly tone. Prioritize clarity and value."
    return "\n".join([doc.page_content for doc, _ in docs])


def generate_blog(
    llm: BaseChatModel,
    topic: str,
    research_summary: str,
    vector_manager: VectorStoreManager,
    brand_name: str,
    history: str = "",
) -> Dict[str, Any]:
    """
    Generate a blog post using research and brand voice.

    Args:
        llm: Chat model.
        topic: Blog topic.
        research_summary: Summary of research findings.
        vector_manager: Vector store for RAG.
        brand_name: Brand identifier for voice retrieval.

    Returns:
        Structured blog output.
    """
    brand_voice = fetch_brand_voice(vector_manager, brand_name)
    messages = [
        SystemMessage(content="Conversation context:\n" + history) if history else None,
        SystemMessage(content=BLOG_PROMPT.format(brand_voice=brand_voice, research_summary=research_summary)),
        HumanMessage(content=f"Write a blog about: {topic}"),
    ]
    messages = [m for m in messages if m]
    response = llm.invoke(messages)
    raw_content = response.content
    if isinstance(raw_content, list):
        # Coerce list outputs (tool calls / structured parts) into a string for parsing
        raw_content = "\n".join([c if isinstance(c, str) else json.dumps(c) for c in raw_content])
    try:
        data = json.loads(raw_content)
    except Exception:
        data = {
            "blog_markdown": raw_content if isinstance(raw_content, str) else str(raw_content),
            "meta_title": topic[:60],
            "meta_description": research_summary[:150],
        }

    vector_manager.add_document(
        "past_outputs",
        content=data.get("blog_markdown", ""),
        metadata={"type": "blog", "topic": topic},
    )
    return data
