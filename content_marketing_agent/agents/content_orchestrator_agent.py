"""Central coordinator: fetch vector context and propagate sanitized fields."""

from __future__ import annotations

import logging

from content_marketing_agent.graph.content_state import ContentState
from content_marketing_agent.services import vector_service

logger = logging.getLogger(__name__)


def content_orchestrator_agent(state: ContentState) -> ContentState:
    """Fetch vector context and propagate sanitized fields."""
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
