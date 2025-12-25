"""Router agent to classify user intent."""

from __future__ import annotations

import json
from typing import Dict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.router_prompt import ROUTER_PROMPT

INTENTS = {"research", "blog", "linkedin", "image", "mixed"}


def classify_intent(llm: BaseChatModel, user_input: str) -> Dict[str, str]:
    """
    Classify the user intent.

    Args:
        llm: Chat model to run the prompt.
        user_input: Raw user request.

    Returns:
        Dictionary containing intent and reason.
    """
    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=user_input),
    ]
    response = llm.invoke(messages)
    try:
        payload = json.loads(response.content)
        intent = payload.get("intent", "").lower()
        if intent not in INTENTS:
            intent = "mixed"
        payload["intent"] = intent
        return payload
    except Exception:
        return {"intent": "mixed", "reason": "Fallback to mixed due to parsing error"}
