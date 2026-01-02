"""Image agent to craft prompts and captions."""

from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Dict, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.graph.content_state import ContentState
from content_marketing_agent.prompts.image_prompt import BLOG_IMAGE_PROMPT

logger = logging.getLogger(__name__)
PLACEHOLDER_IMAGE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAn8B9pCm1N0AAAAASUVORK5CYII="
)


def _parse_images_response(content: Any) -> List[Dict[str, Any]]:
    """Parse LLM JSON or fall back to a single image."""
    try:
        if isinstance(content, list):
            content = "".join(item if isinstance(item, str) else json.dumps(item) for item in content)
        payload = json.loads(content)
        images = payload.get("images") if isinstance(payload, dict) else payload
        return images if isinstance(images, list) else []
    except Exception:
        return []


def _build_genai_client():
    """Return a configured Google GenAI client if available."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.info("Image agent: GOOGLE_API_KEY not set; falling back to placeholders.")
        return None
    try:
        from google import genai
    except Exception as exc:
        logger.warning("Image agent: google-genai package unavailable (%s); using placeholders.", exc)
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        logger.warning("Image agent: failed to init genai client (%s); using placeholders.", exc)
        return None


def _generate_image_data_uri(client, prompt: str) -> str:
    """
    Generate an image via Google GenAI and return a data URI.

    Falls back to a placeholder if generation fails.
    """
    if not client:
        return PLACEHOLDER_IMAGE

    model_name = os.getenv("GEMINI_IMAGE_MODEL", "imagen-4.0-generate-001")
    try: 
        result = client.models.generate_images(model=model_name, prompt=prompt)
        # result.generated_images is the documented field; fall back to .data for older versions
        images = getattr(result, "generated_images", None) or getattr(result, "data", None) or []
        for img in images:
            raw = getattr(img, "image", None) or getattr(img, "image_bytes", None) or getattr(img, "bytes", None)
            if raw:
                if isinstance(raw, dict) and "data" in raw:
                    raw_bytes = raw.get("data")
                else:
                    raw_bytes = raw if isinstance(raw, (bytes, bytearray)) else getattr(raw, "data", b"")
                if raw_bytes:
                    b64 = base64.b64encode(raw_bytes).decode("utf-8")
                    return f"data:image/png;base64,{b64}"
    except Exception as exc:
        logger.warning("Image generation failed for prompt '%s': %s", prompt, exc)

    return PLACEHOLDER_IMAGE


def generate_images_for_blog(
    llm: BaseChatModel,
    blog_markdown: str,
    sections: List[str],
    brand_name: str,
    history: str = "",
) -> List[Dict[str, Any]]:
    """
    Generate multiple image concepts per blog section using a Gemini-backed chat model.

    Returns:
        List of image dictionaries with prompt, caption, alt_text, and image_url.
    """
    if not blog_markdown:
        return []

    brand_voice = f"Professional, clear, and visually engaging tone for {brand_name}."
    section_text = "\n".join(f"- {sec}" for sec in sections if sec) or "General"

    messages = [
        SystemMessage(content="Conversation context:\n" + history) if history else None,
        SystemMessage(
            content=BLOG_IMAGE_PROMPT
            + f"\n\nBrand voice: {brand_voice}\nSections:\n{section_text}\n\nBlog Markdown:\n{blog_markdown}"
        ),
        HumanMessage(content="Return the JSON now."),
    ]
    messages = [m for m in messages if m]
    logger.info("\n\n\n Neeraj inside here 1\n\n")
    response = llm.invoke(messages)
    logger.info("\n\n\n Neeraj inside here 2")
    content = response.content
    images = _parse_images_response(content)

    # Wire in actual image generation when a Google GenAI client is available
    genai_client = _build_genai_client()

    if not images:
        # Fallback: create one prompt per section
        images = [
            {
                "section": sec,
                "prompt": f"Illustration for section '{sec}' inspired by the blog content.",
                "caption": f"Visual for {sec}",
                "alt_text": f"An illustration related to {sec}",
            }
            for sec in (sections or ["Overview"])
        ]

    for img in images:
        prompt_text = img.get("prompt") or "Illustration inspired by the blog content."
        img["image_url"] = img.get("image_url") or _generate_image_data_uri(genai_client, prompt_text)
        img["caption"] = img.get("caption") or img.get("prompt") or "Generated image"
        img["alt_text"] = img.get("alt_text") or "Generated illustration"
        img["section"] = img.get("section") or "General"

    return images


def image_agent_node(state: ContentState) -> ContentState:
    """Generate image assets based on the produced blog content."""
    blog = state.get("blog") or {}
    if not blog:
        logger.info("Image agent skipped: no blog content present in state.")
        return {}

    try:
        from content_marketing_agent.utils.llm_loader import get_chat_model

        llm = get_chat_model(provider="gemini")
        brand_name = state.get("project_title") or "Brand"
        images = generate_images_for_blog(
            llm=llm,
            blog_markdown=blog.get("blog_markdown", ""),
            sections=state.get("sections") or [],
            brand_name=brand_name,
            history=state.get("history", ""),
        )
        logger.info("Image agent generated %s image assets.", len(images))
        return {"images": images}
    except Exception as exc:
        logger.exception("Image agent failed: %s", exc)
        return {"images": []}
