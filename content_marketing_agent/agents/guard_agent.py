"""Guard agent to ensure chat prompts stay relevant to the current research topic."""

from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import HumanMessage

from content_marketing_agent.utils.llm_loader import get_chat_model
from content_marketing_agent.prompts.guard_prompt import GUARD_PROMPT


class GuardState(TypedDict, total=False):
    """State for guarding prompt relevance."""

    prompt: str
    research_output: str
    allowed: bool
    reason: str


def guard_relevance(state: GuardState) -> GuardState:
    """Check if the prompt is relevant to the research output."""
    prompt = (state.get("prompt") or "").strip()
    research_output = (state.get("research_output") or "").strip()
    if not prompt or not research_output:
        return {"allowed": True, "reason": ""}

    guard_prompt = GUARD_PROMPT.format(research_output=research_output, prompt=prompt)
    print("\n\n Guard prompt below \n")
    print(guard_prompt);
    llm = get_chat_model(model="gpt-4o-mini")
    response = llm.invoke([HumanMessage(content=guard_prompt)])
    content = getattr(response, "content", "")
    if isinstance(content, list):
        content = "".join(str(item) for item in content)
    decision = (content or "").strip().lower()
    allowed = "allow" in decision and "reject" not in decision
    return {"allowed": allowed, "reason": decision}
