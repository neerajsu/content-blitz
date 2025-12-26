"""LinkedIn post agent to create platform-optimized copy."""

from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.linkedin_prompt import LINKEDIN_PROMPT


def generate_linkedin(
    llm: BaseChatModel,
    source: str,
    topic: str,
    history: str = "",
) -> Dict[str, Any]:
    """
    Create LinkedIn content from source material.

    Args:
        llm: Chat model.
        source: Blog markdown or research summary.
        topic: Topic for metadata.

    Returns:
        Structured LinkedIn output.
    """
    messages = [
        SystemMessage(content="Conversation context:\n" + history) if history else None,
        SystemMessage(content=LINKEDIN_PROMPT.format(source=source)),
        HumanMessage(content="Create an engaging LinkedIn post and optional carousel outline."),
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
        print("Exception in linkedin_agent when parsing response from llm")
        data = {
            "post": content if isinstance(content, str) else str(content),
            "carousel": "",
        }
    return data
