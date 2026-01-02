"""Intent classification agent for blog and LinkedIn flows."""

from __future__ import annotations

import json
import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from content_marketing_agent.graph.content_state import ContentState
from content_marketing_agent.prompts.intent_prompt import INTENT_PROMPT
from content_marketing_agent.utils.llm_loader import get_chat_model

logger = logging.getLogger(__name__)


def intent_agent(state: ContentState) -> ContentState:
    """Detect whether the user wants LinkedIn, blog, or both."""
    user_prompt = state.get("prompt", "")
    llm = get_chat_model(model="gpt-4o-mini")
    response = llm.invoke([SystemMessage(content=INTENT_PROMPT), HumanMessage(content=user_prompt)])

    content = response.content
    intents: List[str] = []
    try:
        if isinstance(content, list):
            content = "".join(item if isinstance(item, str) else json.dumps(item) for item in content)
        payload = json.loads(content)
        intents_raw = payload.get("intent") or []
        intents = [val for val in intents_raw if isinstance(val, str)]
    except Exception:
        logger.info("Intent agent fallback: defaulting to both intents.")

    normalized = []
    for intent in intents:
        low = intent.lower()
        if low == "linkedin":
            normalized.append("LinkedIn")
        elif low == "blog":
            normalized.append("blog")
    if not normalized:
        normalized = ["LinkedIn", "blog"]
    logger.info("Intent agent decision: %s", normalized)
    return {"intent": normalized}
