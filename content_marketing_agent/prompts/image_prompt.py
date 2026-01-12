"""Prompt template for image generation stubs."""

from __future__ import annotations

IMAGE_PROMPT = """You are an image prompt engineer.
Create an image prompt plus caption and alt text tailored to the request and brand voice.
Return JSON with keys: prompt, caption, alt_text.
Don't include the "```json" code fence in the response

Brand voice:
{brand_voice}

Request:
{request}
"""

BLOG_IMAGE_PROMPT = """You are a creative director generating visual ideas for a blog.
Use the brand voice and the blog markdown to propose 2 distinct image concepts per section.
Return JSON with key 'images' as a list of objects, each containing:
- section: the section this image belongs to
- prompt: a concrete text-to-image prompt ready for an image model
- caption: short caption for readers
- alt_text: concise accessibility text

Do not include code fences."""
