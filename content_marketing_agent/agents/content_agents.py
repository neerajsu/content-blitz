"""Agents powering the content creation LangGraph."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from content_marketing_agent.agents.blog_agent import generate_blog
from content_marketing_agent.agents.linkedin_agent import generate_linkedin
from content_marketing_agent.data_access import research_repository
from content_marketing_agent.graph.content_state import ContentState
from content_marketing_agent.prompts.intent_prompt import INTENT_PROMPT
from content_marketing_agent.prompts.topic_section_generator_prompt import TOPIC_SECTION_GENERATOR_PROMPT
from content_marketing_agent.prompts.topic_sections_prompt import TOPIC_SECTIONS_PROMPT
from content_marketing_agent.services import vector_service
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
        logger.info("Topic and section generator response from llm: ", payload)
        topic = (payload.get("topic") or "").strip()
        sections = [sec.strip() for sec in payload.get("sections") or [] if isinstance(sec, str)]
    except Exception as exc:  # defensive
        logger.warning("Topic generator failed; using prompt fallback. Error: %s", repr(exc))
        topic = user_prompt.strip()
        sections = []

    logger.info("Topic generator decision - topic: '%s', sections: %s", topic, sections)
    return {"topic": topic, "sections": sections, "topic_generation_attempted": True}


def content_orchestrator_agent(state: ContentState) -> ContentState:
    """Central coordinator: fetch vector context and propagate sanitized fields."""
    topic = (state.get("topic") or "").strip() or (state.get("prompt", "").strip()[:80])
    sections = [sec for sec in (state.get("sections") or []) if sec]
    prompt = state.get("prompt", "")
    project_id = state.get("project_id")

    updates: ContentState = {"sections": sections, "topic": topic}

    if topic and project_id and not state.get("vector_documents"):
        query = " ".join([topic, " ".join(sections), prompt]).strip()
        docs = vector_service.query_project_documents(project_id, query=query, k=8)
        logger.info("Orchestrator: retrieved %s vector docs for topic '%s'", len(docs), topic)
        updates["vector_documents"] = docs
    elif not topic:
        logger.info("Orchestrator: topic missing, deferring vector retrieval.")

    return updates


def blog_agent_node(state: ContentState) -> ContentState:
    """Node wrapper around the blog generation agent."""
    try:
        llm = get_chat_model()
        brand_name = state.get("project_title") or "Brand"
        blog = generate_blog(
            llm=llm,
            topic=state.get("topic", ""),
            sections=state.get("sections") or [],
            documents=state.get("vector_documents") or [],
            brand_name=brand_name,
            user_prompt=state.get("prompt", ""),
            history=state.get("history", ""),
        )
        logger.info("Blog agent completed for topic '%s'.", state.get("topic", ""))
        return {"blog": blog}
    except Exception as exc:
        logger.exception("Blog agent failed: %s", exc)
        return {"blog": {}}


def linkedin_agent_node(state: ContentState) -> ContentState:
    """Node wrapper around the LinkedIn generation agent."""
    try:
        llm = get_chat_model()
        linkedin = generate_linkedin(
            llm=llm,
            topic=state.get("topic", ""),
            sections=state.get("sections") or [],
            documents=state.get("vector_documents") or [],
            user_prompt=state.get("prompt", ""),
            history=state.get("history", ""),
        )
        logger.info("LinkedIn agent completed for topic '%s'.", state.get("topic", ""))
        return {"linkedin": linkedin}
    except Exception as exc:
        logger.exception("LinkedIn agent failed: %s", exc)
        return {"linkedin": {}}
