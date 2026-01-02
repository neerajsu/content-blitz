"""Agent to extract topic and sections directly from the user prompt."""

from __future__ import annotations

import json
import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from content_marketing_agent.graph.content_state import ContentState
from content_marketing_agent.prompts.topic_sections_prompt import TOPIC_SECTIONS_PROMPT
from content_marketing_agent.utils.llm_loader import get_chat_model

logger = logging.getLogger(__name__)


def topic_and_sections_agent(state: ContentState) -> ContentState:
    """Extract topic and sections directly from the user prompt."""
    user_prompt = state.get("prompt", "")
    llm = get_chat_model(model="gpt-4o-mini")
    response = llm.invoke([SystemMessage(content=TOPIC_SECTIONS_PROMPT), HumanMessage(content=user_prompt)])

    content = response.content
    topic = ""
    sections: List[str] = []
    try:
        if isinstance(content, list):
            content = "".join(item if isinstance(item, str) else json.dumps(item) for item in content)
        payload = json.loads(content)
        topic = (payload.get("topic") or "").strip()
        sections = [sec.strip() for sec in payload.get("sections") or [] if isinstance(sec, str)]
    except Exception:
        logger.info("Topic extraction fallback: no structured data parsed.")

    logger.info("Topic extraction result - topic: '%s', sections: %s", topic, sections)
    return {"topic": topic, "sections": sections}
