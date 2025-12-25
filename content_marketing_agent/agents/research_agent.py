"""Research agent leveraging SERP and summarization."""

from __future__ import annotations

import json
from typing import Dict, List, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.research_prompt import RESEARCH_PROMPT
from content_marketing_agent.utils.serp import search
from content_marketing_agent.memory.vector_store import VectorStoreManager


def run_research(
    llm: BaseChatModel,
    query: str,
    vector_manager: VectorStoreManager,
    k: int = 5,
    history: str = "",
) -> Dict[str, Any]:
    """
    Execute research: search web, summarize, extract keywords, and cache.

    Args:
        llm: Chat model.
        query: Research query.
        vector_manager: Vector store for caching.
        k: Number of search results.

    Returns:
        Structured research output.
    """
    results = search(query, num_results=k)
    formatted = "\n".join([f"- {item['title']} :: {item['snippet']} ({item['link']})" for item in results])
    messages = [
        SystemMessage(content="Conversation context:\n" + history) if history else None,
        SystemMessage(content=RESEARCH_PROMPT.format(results=formatted)),
        HumanMessage(content="Summarize the above results."),
    ]
    messages = [m for m in messages if m]
    response = llm.invoke(messages)
    try:
        data = json.loads(response.content)
    except Exception:
        data = {
            "summary": response.content,
            "keywords": [],
            "insights": [],
        }

    vector_manager.add_document(
        "research_cache",
        content=data.get("summary", ""),
        metadata={"query": query, "keywords": ",".join(data.get("keywords", []))},
    )
    return {"query": query, "results": results, "analysis": data}
