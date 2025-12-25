"""Image agent to craft prompts and captions."""

from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.prompts.image_prompt import IMAGE_PROMPT
from content_marketing_agent.memory.vector_store import VectorStoreManager


def generate_image_assets(
    llm: BaseChatModel,
    request: str,
    vector_manager: VectorStoreManager,
    brand_name: str,
    history: str = "",
) -> Dict[str, Any]:
    """
    Generate image prompt, caption, and alt text.

    Args:
        llm: Chat model.
        request: Image requirement description.
        vector_manager: Vector store for RAG brand voice.
        brand_name: Brand identifier.

    Returns:
        Structured image output with a stubbed image_url.
    """
    # RAG for brand tone
    docs = vector_manager.search("brand_voice", brand_name, k=2)
    brand_voice = "\n".join([doc.page_content for doc, _ in docs]) if docs else "Professional, clear, engaging."

    messages = [
        SystemMessage(content="Conversation context:\n" + history) if history else None,
        SystemMessage(content=IMAGE_PROMPT.format(brand_voice=brand_voice, request=request)),
        HumanMessage(content="Return JSON as specified."),
    ]
    messages = [m for m in messages if m]
    response = llm.invoke(messages)
    content = response.content
    try:
        if isinstance(content, list):
            content = "".join(
                item if isinstance(item, str) else json.dumps(item) for item in content
            )
        data = json.loads(content)
    except Exception:
        print("Exception in image_agent when parsing response from llm")
        data = {
            "prompt": content if isinstance(content, str) else str(content),
            "caption": f"Image for: {request}",
            "alt_text": f"Illustration related to {request}",
        }

    # Stub image generation; replace with actual API call if configured
    data["image_url"] = data.get("image_url") or "TODO: integrate image generation API"

    vector_manager.add_document(
        "past_outputs",
        content=data.get("caption", ""),
        metadata={"type": "image", "topic": request},
    )
    return data
