"""Image agent to craft prompts and captions."""

from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Dict, List

import requests
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from content_marketing_agent.graph.content_state import ContentState
from content_marketing_agent.prompts.image_prompt import BLOG_IMAGE_PROMPT

logger = logging.getLogger(__name__)
PLACEHOLDER_IMAGE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAn8B9pCm1N0AAAAASUVORK5CYII="
)
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
OPENAI_IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
OPENAI_IMAGE_URL = "https://api.openai.com/v1/images/generations"


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


def _generate_image_data_uri(prompt: str) -> str:
    """
    Generate an image via the OpenAI Images API and return a data URI.

    Falls back to a placeholder if generation fails.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.info("Image agent: OPENAI_API_KEY not set; using placeholder image.")
        return PLACEHOLDER_IMAGE

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "size": OPENAI_IMAGE_SIZE,
    }

    try:
        response = requests.post(OPENAI_IMAGE_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                b64 = first.get("b64_json")
                if b64:
                    return f"data:image/png;base64,{b64}"
                url = first.get("url")
                if url:
                    return url
        logger.warning("OpenAI image response missing b64 data for prompt '%s'.", prompt)
    except (ValueError, TypeError) as exc:
        logger.warning("Failed to parse OpenAI image response for prompt '%s': %s", prompt, exc)
    except requests.HTTPError as exc:
        logger.warning(
            "OpenAI image generation failed for prompt '%s' (status=%s): %s",
            prompt,
            getattr(exc.response, "status_code", "unknown"),
            getattr(exc.response, "text", exc),
        )
    except requests.RequestException as exc:
        logger.warning("OpenAI image generation request error for prompt '%s': %s", prompt, exc)
    except Exception as exc:
        logger.warning("Unexpected error during OpenAI image generation for prompt '%s': %s", prompt, exc)

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
    response = llm.invoke(messages)
    content = response.content
    images = _parse_images_response(content)

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
        img["image_url"] = img.get("image_url") or _generate_image_data_uri(prompt_text)
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
