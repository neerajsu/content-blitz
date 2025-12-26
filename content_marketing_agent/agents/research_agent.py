"""Research agent leveraging Perplexity Sonar (grounded with references)."""

from __future__ import annotations

import json
import os
from typing import Dict, Any, TypedDict

import requests

from content_marketing_agent.prompts.perplexity_prompt import PERPLEXITY_SYSTEM_PROMPT


class ResearchState(TypedDict, total=False):
    """State carried through the research graph."""

    prompt: str
    history: str
    current_output: str
    result: Dict[str, Any]


def _call_perplexity(query: str, history: str = "", current_output: str = "", k: int = 5) -> Dict[str, Any]:
    """Call Perplexity Sonar for grounded research with strict JSON output."""

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return {
            "summary": "",
            "keywords": [],
            "insights": [],
            "references": [],
        }

    user_prompt = "Update the research output based on the user's latest prompt.\n"
    user_prompt += f"Latest prompt: {query}\n"
    if current_output:
        user_prompt += f"\nCurrent research output (markdown):\n{current_output}"
    else:
        user_prompt += "\nCurrent research output (markdown): None yet. Begin a new research output."
    if history:
        user_prompt += f"\n\nConversation context (most recent last):\n{history}"
    user_prompt += (
        "\n\nReturn JSON with fields: summary (markdown), keywords (list of strings), "
        "insights (bullet points), references (list of {title, url, snippet})."
    )

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": PERPLEXITY_SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,   # lower = more deterministic JSON
        "top_p": 0.9,
    }

    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Hard fallback (should be rare if prompt is respected)
        return {
            "summary": content,
            "keywords": [],
            "insights": [],
            "references": [],
        }


def run_research(
    query: str,
    k: int = 5,
    history: str = "",
    current_output: str = "",
) -> Dict[str, Any]:
    """
    Execute research via Perplexity Sonar (grounded with references).

    Args:
        query: Research query.
        k: Number of search results.
        history: Conversation history text.
        current_output: Existing research markdown to update.

    Returns:
        Structured research output.
    """
    try:
        analysis = _call_perplexity(query, history=history, current_output=current_output, k=k)
    except requests.RequestException as exc:
        # Gracefully handle upstream errors and return a structured fallback
        analysis = {
            "summary": f"Perplexity API error: {exc}",
            "keywords": [],
            "insights": [],
            "references": [],
        }

    return {"query": query, "analysis": analysis}


def research_step(state: ResearchState) -> ResearchState:
    """Invoke the research agent and return updated state."""
    prompt = state.get("prompt", "")
    history = state.get("history", "")
    current_output = state.get("current_output", "")
    result = run_research(prompt, history=history, current_output=current_output)
    return {"result": result}
