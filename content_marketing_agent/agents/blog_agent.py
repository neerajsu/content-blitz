"""Blog writing agent that applies brand voice without external retrieval."""

from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.blog_prompt import BLOG_PROMPT


def generate_blog(
    llm: BaseChatModel,
    topic: str,
    research_summary: str,
    brand_name: str,
    history: str = "",
) -> Dict[str, Any]:
    """
    Generate a blog post using research and brand voice.

    Args:
        llm: Chat model.
        topic: Blog topic.
        research_summary: Summary of research findings.
        brand_name: Brand identifier for voice retrieval.

    Returns:
        Structured blog output.
    """
    brand_voice = f"Maintain a consistent professional yet friendly tone for {brand_name}. Prioritize clarity and value."
    messages = [
        SystemMessage(content="Conversation context:\n" + history) if history else None,
        SystemMessage(content=BLOG_PROMPT.format(brand_voice=brand_voice, research_summary=research_summary)),
        HumanMessage(content=f"Write a blog about: {topic}"),
    ]
    messages = [m for m in messages if m]
    response = llm.invoke(messages)
    content = response.content
    try:
        if isinstance(content, list):
            content = "".join(
                item if isinstance(item, str) else json.dumps(item) for item in content
            )    
        data = json.loads(content)
    except Exception:
        print("Exception in blog_agent when parsing response from llm")
        data = {
            "blog_markdown": content if isinstance(content, str) else str(content),
            "meta_title": topic[:60],
            "meta_description": research_summary[:150],
        }

    return data
