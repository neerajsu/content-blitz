"""Agent to generate topic and sections when missing using research metadata."""

from __future__ import annotations

import json
import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from content_marketing_agent.data_access import research_repository
from content_marketing_agent.graph.content_state import ContentState
from content_marketing_agent.prompts.topic_section_generator_prompt import TOPIC_SECTION_GENERATOR_PROMPT
from content_marketing_agent.utils.llm_loader import get_chat_model

logger = logging.getLogger(__name__)


def topic_and_section_generator_agent(state: ContentState) -> ContentState:
    """Generate topic and sections from research metadata when missing."""
    project_id = state.get("project_id")
    user_prompt = state.get("prompt", "")
    if not project_id:
        logger.info("Topic generator: missing project_id; returning empty topic/sections.")
        return {"topic": "", "sections": []}

    research_docs = research_repository.list_research_outputs(project_id)
    if not research_docs:
        logger.info("Topic generator: no research outputs found; falling back to user prompt.")
        return {"topic": user_prompt.strip(), "sections": []}

    lines = []
    for idx, doc in enumerate(research_docs, 1):
        summary = doc.get("summary") or ""
        structured = doc.get("structured") or {}
        keywords = structured.get("keywords") or []
        insights = structured.get("insights") or []
        lines.append(
            f"Document {idx} Summary: {summary}\n"
            f"Keywords: {', '.join(keywords)}\n"
            f"Insights: {' | '.join(insights)}"
        )
    metadata_corpus = "\n\n".join(lines)

    topic = ""
    sections: List[str] = []
    try:
        llm = get_chat_model(model="gpt-4o-mini")
        response = llm.invoke(
            [
                SystemMessage(content=TOPIC_SECTION_GENERATOR_PROMPT.format(metadata_corpus=metadata_corpus)),
                HumanMessage(content="Propose a grounded topic and outline."),
            ]
        )
        content = response.content
        if isinstance(content, list):
            content = "".join(item if isinstance(item, str) else json.dumps(item) for item in content)
        payload = json.loads(content)
        logger.info("Topic and section generator response from llm: %s", payload)
        topic = (payload.get("topic") or "").strip()
        sections = [sec.strip() for sec in payload.get("sections") or [] if isinstance(sec, str)]
    except Exception as exc:  # defensive
        logger.warning("Topic generator failed; using prompt fallback. Error: %s", repr(exc))
        topic = user_prompt.strip()
        sections = []

    logger.info("Topic generator decision - topic: '%s', sections: %s", topic, sections)
    return {"topic": topic, "sections": sections, "topic_generation_attempted": True}
