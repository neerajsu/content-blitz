"""Research agent leveraging Perplexity Sonar (grounded with references)."""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Any

import requests

from content_marketing_agent.prompts.perplexity_prompt import PERPLEXITY_SYSTEM_PROMPT
from content_marketing_agent.memory.vector_store import VectorStoreManager


def _call_perplexity(query: str, history: str = "", k: int = 5) -> Dict[str, Any]:
    """Call Perplexity Sonar for grounded research with references."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return {}

    system_prompt = PERPLEXITY_SYSTEM_PROMPT
    user_prompt = f"Research query: {query}"
    if history:
        user_prompt += f"\n\nConversation context:\n{history}"

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "top_p": 0.9,
    }
    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    print(content);

    if isinstance(content, str):
        fenced = re.match(r"```(?:json)?\s*(.*)```", content, flags=re.DOTALL)
        if fenced:
            content = fenced.group(1).strip()
        try:
            return json.loads(content)
        except Exception:
            return {"summary": content, "keywords": [], "insights": [], "references": []}
    return {"summary": str(content), "keywords": [], "insights": [], "references": []}


def run_research(
    query: str,
    vector_manager: VectorStoreManager,
    k: int = 5,
    history: str = "",
) -> Dict[str, Any]:
    """
    Execute research via Perplexity Sonar (grounded with references).

    Args:
        query: Research query.
        vector_manager: Vector store for caching.
        k: Number of search results.
        history: Conversation history text.

    Returns:
        Structured research output.
    """
    try:
        analysis = _call_perplexity(query, history=history, k=k)
        results = analysis.get("references", [])
    except requests.RequestException as exc:
        # Gracefully handle upstream errors and return a structured fallback
        analysis = {
            "summary": f"Perplexity API error: {exc}",
            "keywords": [],
            "insights": [],
            "references": [],
        }
        results = []

    vector_manager.add_document(
        "research_cache",
        content=analysis.get("summary", ""),
        metadata={"query": query, "keywords": ",".join(analysis.get("keywords", []))},
    )
    return {"query": query, "analysis": analysis}
