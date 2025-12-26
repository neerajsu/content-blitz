"""Agent for generating concise titles from research summaries."""

from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import HumanMessage

from content_marketing_agent.utils.llm_loader import get_chat_model


class TitleState(TypedDict, total=False):
    """State for title generation from a research summary."""

    summary: str
    title: str


def generate_title(state: TitleState) -> TitleState:
    """Generate a concise title from the research summary."""
    summary = (state.get("summary") or "").strip()
    if not summary:
        return {"title": ""}

    prompt = (
        "Generate a concise, 3-6 word title for the following research summary. "
        "Return only the title with no quotes.\n\nSummary:\n" + summary
    )
    llm = get_chat_model(model="gpt-5-nano")
    response = llm.invoke([HumanMessage(content=prompt)])
    content = getattr(response, "content", "")
    if isinstance(content, list):
        content = "".join(str(item) for item in content)
    title = (content or "").strip()
    return {"title": title}
