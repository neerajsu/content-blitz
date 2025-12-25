"""LinkedIn post agent to create platform-optimized copy."""

from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.linkedin_prompt import LINKEDIN_PROMPT
from content_marketing_agent.memory.vector_store import VectorStoreManager


def generate_linkedin(
    llm: BaseChatModel,
    source: str,
    vector_manager: VectorStoreManager,
    topic: str,
    history: str = "",
) -> Dict[str, Any]:
    """
    Create LinkedIn content from source material.

    Args:
        llm: Chat model.
        source: Blog markdown or research summary.
        vector_manager: Vector store for logging past outputs.
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
    raw_content = response.content
    if isinstance(raw_content, list):
        raw_content = "\n".join([c if isinstance(c, str) else json.dumps(c) for c in raw_content])
    try:
        data = json.loads(raw_content)
    except Exception:
        data = {
            "post": raw_content if isinstance(raw_content, str) else str(raw_content),
            "carousel": "",
        }

    vector_manager.add_document(
        "past_outputs",
        content=data.get("post", ""),
        metadata={"type": "linkedin", "topic": topic},
    )
    return data
