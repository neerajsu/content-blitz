"""Blog writing agent that applies brand voice with retrieved context."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.blog_prompt import BLOG_PROMPT

logger = logging.getLogger(__name__)


def _format_context(documents: Iterable[Document]) -> str:
    docs = list(documents)
    if not docs:
        logger.info("Blog agent: no vector documents available; relying on prompt alone.")
        return "No additional research context available."

    snippets = []
    for idx, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        chat_id = meta.get("chat_id")
        header = f"Document {idx}" + (f" (chat {chat_id})" if chat_id else "")
        snippets.append(f"{header}:\n{doc.page_content}")
    return "\n\n".join(snippets)


def generate_blog(
    llm: BaseChatModel,
    topic: str,
    sections: list[str],
    documents: Iterable[Document],
    brand_name: str,
    user_prompt: str,
    history: str = "",
) -> Dict[str, Any]:
    """Generate a blog post using vector-grounded context."""

    brand_voice = f"Maintain a consistent professional yet friendly tone for {brand_name}. Prioritize clarity and value."
    context = _format_context(documents)
    sections = [sec for sec in sections if sec]
    messages = [
        SystemMessage(content="Conversation context:\n" + history) if history else None,
        SystemMessage(
            content=BLOG_PROMPT.format(
                brand_voice=brand_voice,
                topic=topic,
                sections=sections,
                context=context,
                user_prompt=user_prompt,
            )
        ),
        HumanMessage(content="Draft the blog now."),
    ]
    messages = [m for m in messages if m]
    response = llm.invoke(messages)
    content = response.content
    try:
        if isinstance(content, list):
            content = "".join(item if isinstance(item, str) else json.dumps(item) for item in content)
        data = json.loads(content)
    except Exception:
        logger.exception("Exception in blog_agent when parsing response from llm")
        data = {
            "blog_markdown": content if isinstance(content, str) else str(content),
            "meta_title": (topic or "Blog")[:60],
            "meta_description": user_prompt[:150],
        }

    return data
