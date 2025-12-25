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
